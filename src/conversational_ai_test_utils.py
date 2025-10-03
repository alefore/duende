from conversation import Conversation, Message, ContentSection
from conversational_ai import ConversationalAI, ConversationalAIConversation


class FakeConversationalAIConversation(ConversationalAIConversation):
  """A fake implementation of ConversationalAIConversation for testing."""

  def __init__(self, conversation: Conversation,
               scripted_responses: list[Message]):
    self.conversation = conversation
    self.scripted_responses = scripted_responses

  async def SendMessage(self, message: Message) -> Message:
    # Add the incoming message to the conversation history.
    await self.conversation.AddMessage(message)

    if not self.scripted_responses:
      raise StopIteration(
          "No more scripted responses. "
          "This probably means the test expected the AgentLoop to stop conversing but the AgentLoop did not."
      )

    response_message = self.scripted_responses.pop(0)

    # Add the assistant's response to the conversation history.
    await self.conversation.AddMessage(response_message)
    return response_message


class FakeConversationalAI(ConversationalAI):
  """A fake implementation of ConversationalAI for testing."""

  def __init__(self, scripted_responses: dict[str, list[Message]]):
    self.scripted_responses = scripted_responses
    # Keep track of which conversations have been started to help debugging
    self.started_conversations: dict[str, int] = {}

  def StartConversation(
      self, conversation: Conversation) -> ConversationalAIConversation:
    name = conversation.GetName()
    if name not in self.scripted_responses:
      raise KeyError(
          f"The conversation name '{name}' is not a key in the scripted_responses dictionary. "
          f"Started conversations so far: {list(self.started_conversations.keys())}"
      )
    self.started_conversations[name] = conversation.GetId()
    return FakeConversationalAIConversation(conversation,
                                            self.scripted_responses[name])
