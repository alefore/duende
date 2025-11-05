import logging

from conversation import Conversation, Message, ContentSection
from conversational_ai import ConversationalAI, ConversationalAIConversation


class FakeConversationalAIConversation(ConversationalAIConversation):
  """A fake implementation of ConversationalAIConversation for testing."""

  def __init__(self, conversation: Conversation,
               scripted_responses: list[Message]):
    self.conversation = conversation
    self.scripted_responses = scripted_responses
    for message in scripted_responses:
      if message.role != "assistant":
        raise ValueError(
            "A test has incorrectly included a message with an unexpected role "
            f"(role={message.role}) "
            "in the scripted responses of a FakeconversationalAIConversation. "
            "Only responses *from the AI to Duende* "
            "(role=assistant) should be included, "
            "not messages *from Duende to the AI*.")
      for section in message.GetContentSections():
        if section.command_output:
          raise ValueError(
              "A test has incorrectly included a message with a content "
              "section that includes an unexpected `command_output` field. "
              "That is incorrect because the AI never issues commands with "
              "these values to Duende (which is what the scripted responses "
              "in FakeConversationalAIConversation simulates). The test "
              "probably meant to trigger execution of an AgentCommand, in "
              "which case it should include a message with a `command` field "
              f"instead. The incorrect section is: {section}")
    logging.info(f"Started fake conversation with {len(scripted_responses)=}")

  async def SendMessage(self, message: Message) -> Message:
    # Add the incoming message to the conversation history.
    await self.conversation.AddMessage(message)

    if not self.scripted_responses:
      logging.info(f"Fake conversation: received unexpected message: {message}")
      raise StopIteration(
          "No more scripted responses. "
          "This probably means the test expected the AgentLoop "
          "to stop conversing but the AgentLoop did not. "
          "That might mean that the last command you added to the conversation "
          "did not succeed, so the AgentLoop continues to run (as expected). "
          "Your test may need to add an additional command "
          "that passes validation in order to cause the AgentLoop "
          "to terminate successfully. "
          f"The last message from Duende to the AI was this: {message}")

    response_message = self.scripted_responses.pop(0)
    logging.info(
        f"Fake conversation: received {message}, response {response_message}")

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
