from google import genai
import logging
import asyncio
import sys
from typing import cast, Any, Coroutine, Dict, List, Optional

from command_registry import CommandRegistry
from agent_command import CommandInput, CommandSyntax
from conversation import Conversation
from message import Message, ContentSection
from conversational_ai import ConversationalAI, ConversationalAIConversation


def _parse_syntax(syntax: CommandSyntax) -> genai.types.FunctionDeclaration:
  return genai.types.FunctionDeclaration(
      description=syntax.description,
      name=syntax.name,
      parameters=genai.types.Schema(
          type=genai.types.Type.OBJECT,
          properties={
              arg.name:
                  genai.types.Schema(
                      type=genai.types.Type.STRING, description=arg.description)
              for arg in syntax.arguments
          },
          required=[arg.name for arg in syntax.arguments if arg.required]),
      response=genai.types.Schema(
          type=genai.types.Type.STRING,
          description=syntax.output_description or ''))


def _get_config(registry: CommandRegistry) -> genai.types.GenerateContentConfig:

  return genai.types.GenerateContentConfig(
      automatic_function_calling=genai.types.AutomaticFunctionCallingConfig(
          disable=True),
      tools=[
          genai.types.Tool(function_declarations=[
              _parse_syntax(c.Syntax()) for c in registry.GetCommands()
          ])
      ])


class GeminiConversation(ConversationalAIConversation):

  def __init__(self, client: genai.Client, registry: CommandRegistry,
               model_name: str, conversation: Conversation) -> None:
    self.client = client
    self.conversation = conversation

    logging.info(f"Starting Gemini conversation")
    config = _get_config(registry)
    logging.info(config)
    self.chat = self.client.chats.create(model=model_name, config=config)

  def SendMessage(self, message: Message) -> Message:
    self.conversation.AddMessage(message)

    gemini_parts: List[str | genai.types.Part] = []
    for section in message.GetContentSections():
      if section.content:
        gemini_parts.append(section.content)
      if section.command_output:
        assert section.command_output.command_name
        response_dict = {"output": section.command_output.output}
        if section.command_output.errors:
          response_dict['errors'] = section.command_output.errors
        gemini_parts.append(
            genai.types.Part.from_function_response(
                name=section.command_output.command_name,
                response=response_dict))

    log_content = "\n".join(
        [s.content for s in message.GetContentSections() if s.content])
    logging.info(
        f"Sending message to Gemini: '{gemini_parts}' (with {len(gemini_parts)} parts)"
    )

    try:
      response = self.chat.send_message(gemini_parts)  # type: ignore[arg-type]
      logging.info(f"XXX Response: {response}")
    except Exception as e:
      logging.exception("Failed to communicate with Gemini API.")
      raise e

    reply_message = Message(role="assistant")
    if response.text:
      logging.info(f"Text received from Gemini: '{response.text[:50]}...'")
      reply_message.PushSection(
          ContentSection(content=response.text, summary=None))
    if response.candidates:
      if response.candidates[0].content and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
          logging.info(part)
          if part.function_call:
            logging.info(f"Commands received from Gemini")
            function_call: genai.types.FunctionCall = part.function_call
            logging.info(function_call)
            logging.info(function_call.args)
            reply_message.PushSection(
                ContentSection(
                    content="",
                    summary=f'MCP call: {function_call}',
                    command=CommandInput(
                        command_name=(function_call.name or "unknown"),
                        args=(function_call.args or {}))))
    else:
      logging.fatal(f'Invalid response: {response}')

    self.conversation.AddMessage(reply_message)
    return reply_message


class Gemini(ConversationalAI):

  def __init__(self, api_key_path: str, model_name: str,
               registry: CommandRegistry) -> None:
    with open(api_key_path, 'r') as f:
      api_key = f.read().strip()
    self.client = genai.Client(api_key=api_key)
    # genai.configure(api_key=api_key)  # type: ignore[attr-defined]
    if model_name == "gemini-LIST":
      self._ListModels()
      sys.exit(0)
    self.model_name = model_name
    self.command_registry = registry
    logging.info(f"Initialized Gemini AI with model: {self.model_name}")

  def StartConversation(
      self, conversation: Conversation) -> ConversationalAIConversation:
    return GeminiConversation(
        self.client,
        self.command_registry,
        self.model_name,
        conversation=conversation)

  def _ListModels(self) -> None:
    for m in genai.list_models():  # type: ignore[attr-defined]
      if "generateContent" in m.supported_generation_methods:
        print(f"Name: {m.name}")
        print(f"  Display Name: {m.display_name}")
        print(f"  Description: {m.description}")
        print(f"  Input Token Limit: {m.input_token_limit}")
        print(f"  Output Token Limit: {m.output_token_limit}")
        print("-" * 20)
