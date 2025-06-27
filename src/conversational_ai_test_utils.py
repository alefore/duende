from conversation import Conversation, Message, ContentSection
from conversational_ai import ConversationalAI, ConversationalAIConversation


class FakeConversationalAIConversation(ConversationalAIConversation):
  """A fake implementation of ConversationalAIConversation for testing."""

  def __init__(self, scripted_responses):
    self._scripted_responses = scripted_responses
    self._response_index = 0
    self.send_message_calls = 0

  def SendMessage(self, message: Message) -> Message:
    self.send_message_calls += 1
    if self._response_index < len(self._scripted_responses):
      response_content = self._scripted_responses[self._response_index]
      self._response_index += 1
      response_message = Message(
          role='assistant',
          content_sections=[ContentSection(content=[response_content])])
      return response_message
    raise StopIteration("No more scripted responses.")


class FakeConversationalAI(ConversationalAI):
  """A fake implementation of ConversationalAI for testing."""

  def __init__(self, scripted_responses):
    self._scripted_responses = scripted_responses
    self.last_conversation = None

  def StartConversation(
      self, conversation: Conversation) -> ConversationalAIConversation:
    self.last_conversation = FakeConversationalAIConversation(
        self._scripted_responses)
    return self.last_conversation
