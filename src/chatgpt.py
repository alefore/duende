from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from typing import cast, Optional
from conversation import Message, Conversation
from conversational_ai import ConversationalAI, ConversationalAIConversation
import logging


class ChatGPTConversation(ConversationalAIConversation):

  def __init__(self, client: OpenAI, model: str,
               conversation: Optional[Conversation]):
    self.client = client
    self.model = model
    self.conversation = conversation or Conversation()
    logging.info(f"Starting conversation, "
                 f"messages: {len(self.conversation.GetMessagesList())}")

  def SendMessage(self, message: Message) -> Message:
    self.conversation.AddMessage(message)

    openai_messages: list[ChatCompletionMessageParam] = [
        cast(ChatCompletionMessageParam, {
            "role": m.role,
            "content": m.content
        }) for m in self.conversation.GetMessagesList()
    ]

    logging.info("Sending message to ChatGPT.")
    try:
      response = self.client.chat.completions.create(
          model=self.model, messages=openai_messages)
    except Exception as e:
      logging.exception("Failed to communicate with OpenAI.")
      raise e

    logging.info("Received response from ChatGPT.")

    reply_content = response.choices[0].message.content or ""
    reply_message = Message(role="assistant", content=reply_content)
    self.conversation.AddMessage(reply_message)
    return reply_message


class ChatGPT(ConversationalAI):

  def __init__(self, api_key_path: str, model: str = "gpt-4"):
    with open(api_key_path, 'r') as f:
      api_key = f.read().strip()
    self.client = OpenAI(api_key=api_key)
    self.model = model

  def StartConversation(
      self,
      conversation: Optional[Conversation]) -> ConversationalAIConversation:
    return ChatGPTConversation(
        client=self.client, model=self.model, conversation=conversation)
