from typing import Optional

from conversation import Conversation, Message, ContentSection
from conversational_ai import ConversationalAI, ConversationalAIConversation


class FakeConversationalAIConversation(ConversationalAIConversation):
  """A fake implementation of ConversationalAIConversation for testing."""

  def __init__(self, conversation: Conversation, scripted_responses: list[str]):
    self.conversation = conversation
    self.scripted_responses = scripted_responses
    self.send_message_calls = 0

  def SendMessage(self, message: Message) -> Message:
    self.send_message_calls += 1

    # Add the incoming message to the conversation history.
    self.conversation.AddMessage(message)

    if not self.scripted_responses:
      raise StopIteration("No more scripted responses.")

    response_text = self.scripted_responses.pop(0)
    response_message = Message(
        role='assistant',
        content_sections=[ContentSection(content=[response_text])])

    # Add the assistant's response to the conversation history.
    self.conversation.AddMessage(response_message)
    return response_message


class FakeConversationalAI(ConversationalAI):
  """A fake implementation of ConversationalAI for testing."""

  def __init__(self, scripted_responses: list[str]):
    self.scripted_responses = scripted_responses
    self.last_conversation: Optional[FakeConversationalAIConversation] = None

  def StartConversation(
      self, conversation: Conversation) -> ConversationalAIConversation:
    output = FakeConversationalAIConversation(conversation,
                                              self.scripted_responses)
    self.last_conversation = output
    return output
