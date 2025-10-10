import asyncio
from google import genai
import logging
import sys
from typing import Any

from command_registry import CommandRegistry
from agent_command import ArgumentContentType, CommandInput, CommandSyntax, VariableMap, VariableName, VariableValue, VariableValueInt, VariableValueStr
from conversation import Conversation
from message import Message, ContentSection
from conversational_ai import ConversationalAI, ConversationalAIConversation
import tenacity


def _parse_arg_type(arg: ArgumentContentType) -> genai.types.Type:
  if arg == ArgumentContentType.INTEGER:
    return genai.types.Type.INTEGER
  return genai.types.Type.STRING


def _parse_syntax(syntax: CommandSyntax) -> genai.types.FunctionDeclaration:
  return genai.types.FunctionDeclaration(
      description=syntax.description,
      name=syntax.name,
      parameters=genai.types.Schema(
          type=genai.types.Type.OBJECT,
          properties={
              arg.name:
                  genai.types.Schema(
                      type=_parse_arg_type(arg.arg_type),
                      description=arg.description) for arg in syntax.arguments
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

  def __init__(self, client: genai.Client, model_name: str,
               conversation: Conversation) -> None:
    self.client = client
    self.conversation = conversation

    logging.info(f"Starting Gemini conversation")
    config = _get_config(conversation.command_registry)
    logging.info(config)
    self.chat = self.client.aio.chats.create(model=model_name, config=config)

  @tenacity.retry(
      wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
      stop=tenacity.stop_after_attempt(5),
      retry=tenacity.retry_if_exception_type(Exception),
      before_sleep=tenacity.before_sleep_log(logging.root, logging.INFO))
  async def _send_message_with_retries(
      self,
      gemini_parts: list[genai.types.Part | str | genai.types.PartDict]) -> Any:
    return await self.chat.send_message(list(gemini_parts))

  async def SendMessage(self, message: Message) -> Message:
    await self.conversation.AddMessage(message)

    gemini_parts: list[genai.types.Part | str | genai.types.PartDict] = []
    for section in message.GetContentSections():
      if section.content:
        gemini_parts.append(section.content)
      if section.command_output:
        assert section.command_output.command_name
        response_dict = {"output": section.command_output.output}
        if section.command_output.errors:
          response_dict['errors'] = section.command_output.errors

        gemini_parts.append(
            genai.types.Part(
                function_response=genai.types.FunctionResponse(
                    name=section.command_output.command_name,
                    response=response_dict),
                thought_signature=section.command_output.thought_signature))

    log_content = "\n".join(
        [s.content for s in message.GetContentSections() if s.content])
    logging.info(
        f"Sending message to Gemini: '{gemini_parts}' (with {len(gemini_parts)} parts)"
    )

    try:
      # We have to call `list(…)` around `gemini_parts` because list is not
      # covariant:
      # https://mypy.readthedocs.io/en/stable/common_issues.html#variance
      response = await self._send_message_with_retries(list(gemini_parts))
      logging.info(f"Response: {response}")
    except Exception as e:
      logging.exception("Failed to communicate with Gemini API.")
      raise e

    reply_message = Message(role="assistant")
    if response.text:
      logging.info(f"Text received from Gemini: '{response.text[:50]}...'")
      reply_message.PushSection(
          ContentSection(content=response.text, summary=None))
    if not response.candidates:
      logging.fatal(f'Invalid response: {response}')
      return reply_message  # Never executed.

    if response.candidates[0].content and response.candidates[0].content.parts:
      for part in response.candidates[0].content.parts:
        logging.info(part)
        if not part.function_call:
          continue
        name = part.function_call.name
        if not name:
          continue

        logging.info(f"Commands received from Gemini")
        function_call: genai.types.FunctionCall = part.function_call
        logging.info(function_call)
        logging.info(function_call.args)

        reply_message.PushSection(
            ContentSection(
                content="",
                summary=f'MCP call: {function_call}',
                command=CommandInput(
                    command_name=name,
                    args=VariableMap({
                        VariableName(k): _get_value(v)
                        for k, v in (function_call.args or {}).items()
                    }),
                    thought_signature=(part.thought_signature if hasattr(
                        part, 'thought_signature') else None))))

    await self.conversation.AddMessage(reply_message)
    return reply_message


def _get_value(v: Any) -> VariableValue:
  match v:
    case str(s):
      return VariableValueStr(s)
    case int(i):
      return VariableValueInt(i)
    case _:
      raise ValueError(f"Unsupported data type: {v}")


class Gemini(ConversationalAI):

  def __init__(
      self,
      api_key_path: str,
      model_name: str,
  ) -> None:
    with open(api_key_path, 'r') as f:
      api_key = f.read().strip()
    self.client = genai.Client(api_key=api_key)
    # genai.configure(api_key=api_key)  # type: ignore[attr-defined]
    if model_name == "gemini-LIST":
      self._ListModels()
      sys.exit(0)
    self.model_name = model_name
    logging.info(f"Initialized Gemini AI with model: {self.model_name}")

  def StartConversation(
      self, conversation: Conversation) -> ConversationalAIConversation:
    return GeminiConversation(
        self.client, self.model_name, conversation=conversation)

  def _ListModels(self) -> None:
    for m in genai.list_models():  # type: ignore[attr-defined]
      if "generateContent" in m.supported_generation_methods:
        print(f"Name: {m.name}")
        print(f"  Display Name: {m.display_name}")
        print(f"  Description: {m.description}")
        print(f"  Input Token Limit: {m.input_token_limit}")
        print(f"  Output Token Limit: {m.output_token_limit}")
        print("-" * 20)
