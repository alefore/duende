import google.generativeai as genai
import google.generativeai.types as genai_types
import logging
import asyncio
import sys
from typing import cast, Any, Coroutine, Dict, List, Optional

from conversation import Conversation, Message, MultilineContent, ContentSection
from conversational_ai import ConversationalAI, ConversationalAIConversation


class GeminiConversation(ConversationalAIConversation):

  def __init__(self, model: genai.GenerativeModel,
               conversation: Conversation) -> None:
    self.model = model
    self.conversation = conversation

    gemini_initial_history: List[genai_types.ContentDict] = []
    for msg in self.conversation.GetMessagesList():
      gemini_role = "model" if msg.role == "assistant" else msg.role
      parts = [{"text": "\n".join(s.content)} for s in msg.GetContentSections()]
      gemini_initial_history.append(
          cast(genai_types.ContentDict, {
              "role": gemini_role,
              "parts": parts
          }))

    self.chat = self.model.start_chat(history=gemini_initial_history)

    logging.info(
        f"Starting Gemini conversation with {len(gemini_initial_history)} "
        f"initial messages.")

  def SendMessage(self, message: Message) -> Message:
    self.conversation.AddMessage(message)

    # Prepare message content for Gemini by transforming sections into parts
    gemini_parts = []
    for section in message.GetContentSections():
      gemini_parts.append({"text": "\n".join(section.content)})

    log_content = '\n'.join(
        ['\n'.join(s.content) for s in message.GetContentSections()])
    logging.info(
        f"Sending message to Gemini: '{log_content[:50]}...' (with {len(gemini_parts)} parts)"
    )

    try:
      response = self.chat.send_message(gemini_parts)
      reply_content = response.text

    except Exception as e:
      logging.exception("Failed to communicate with Gemini API.")
      raise e

    logging.info(f"Received response from Gemini: '{reply_content[:50]}...'")

    reply_message = Message(
        role="assistant", content_sections=[ContentSection(content=[reply_content], summary=None)])
    self.conversation.AddMessage(reply_message)
    return reply_message


class Gemini(ConversationalAI):

  def __init__(self, api_key_path: str, model_name: str = "gemini-pro"):
    with open(api_key_path, 'r') as f:
      api_key = f.read().strip()
    genai.configure(api_key=api_key)
    if model_name == "gemini-LIST":
      self._ListModels()
      sys.exit(0)
    self.model = genai.GenerativeModel(model_name)
    self.model_name = model_name
    logging.info(f"Initialized Gemini AI with model: {self.model_name}")

  def StartConversation(
      self, conversation: Conversation) -> ConversationalAIConversation:
    return GeminiConversation(model=self.model, conversation=conversation)

  def _ListModels(self):
    for m in genai.list_models():
      if "generateContent" in m.supported_generation_methods:
        print(f"Name: {m.name}")
        print(f"  Display Name: {m.display_name}")
        print(f"  Description: {m.description}")
        print(f"  Input Token Limit: {m.input_token_limit}")
        print(f"  Output Token Limit: {m.output_token_limit}")
        print("-" * 20)
