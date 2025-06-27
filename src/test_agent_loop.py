import unittest
from unittest.mock import MagicMock

from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax
from agent_loop import AgentLoop
from agent_loop_options import AgentLoopOptions
from command_registry import CommandRegistry
from conversation import Conversation, ConversationFactory, Message, ContentSection
from conversational_ai_test_utils import FakeConversationalAI
from file_access_policy import FileAccessPolicy


class TestAgentLoop(unittest.TestCase):
  """Tests the main AgentLoop execution flow."""

  def setUp(self):
    """Set up common stateless mocks for all tests."""
    # Mock the list_files command
    # TODO: This is ugly, we shouldn't use a mock, just a real CommandSyntax.
    mock_syntax = MagicMock(spec=CommandSyntax)
    mock_syntax.multiline = None
    mock_syntax.required = []
    mock_syntax.optional = []
    mock_syntax.repeatable_final = None

    self.mock_list_files_command = MagicMock(spec=AgentCommand)
    self.mock_list_files_command.Name.return_value = "list_files"
    self.mock_list_files_command.Aliases.return_value = set()
    self.mock_list_files_command.Syntax.return_value = mock_syntax
    self.mock_list_files_command.Execute.return_value = CommandOutput(
        output=["src/agent_loop.py"], errors=[], summary="Listed 1 file.")

    self.registry = CommandRegistry()
    self.registry.Register(self.mock_list_files_command)

    # Mock other dependencies
    self.mock_confirmation_state = MagicMock()
    self.mock_confirmation_state.RequireConfirmation.return_value = ""

    # TODO: This also shouldn't use mock but a real conversation factory.
    self.mock_conv_factory = MagicMock(spec=ConversationFactory)

    # TODO: This also shouldn't use mock but a real conversation factory.
    self.mock_file_access_policy = MagicMock(spec=FileAccessPolicy)

  def _create_agent_loop_for_test(self,
                                  scripted_responses: list[str]) -> AgentLoop:
    """Creates an AgentLoop instance with a scripted AI for testing."""
    self.fake_ai = FakeConversationalAI(scripted_responses=scripted_responses)

    # TODO: Retain the Conversation() given in a self.conversation parameter.
    # Use that instead of self.fake_ai.last_conversation to validate
    # expectations about the conversation. We should get rid of
    # FakeConversationaAI.last_conversation altogether.
    options = AgentLoopOptions(
        task_prompt_content=["Test task"],
        conversation_factory=self.mock_conv_factory,
        conversation_path="/tmp/test_conversation.json",
        model="test-model",
        # Use a fresh conversation for each test to prevent state leakage
        conversation=Conversation(unique_id=0, name="test-name"),
        start_message=Message(
            role='user',
            content_sections=[ContentSection(content=["Test Task"])]),
        commands_registry=self.registry,
        confirmation_state=self.mock_confirmation_state,
        file_access_policy=self.mock_file_access_policy,
        conversational_ai=self.fake_ai,
        confirm_done=False,
        skip_implicit_validation=True,
    )
    return AgentLoop(options)

  def test_run_loop_with_simple_command_and_done(self):
    """
    Tests a simple interaction where the AI issues one command and then #done.
    """
    # 1. Setup: Create AgentLoop with a scripted AI.
    agent_loop = self._create_agent_loop_for_test(
        scripted_responses=["#list_files", "#done"])

    # 2. Run the agent loop.
    agent_loop.run()

    # 3. Assertions: Verify the loop behaved as expected.
    self.assertIsNotNone(self.fake_ai.last_conversation)
    # The AI is called once with the start message, and a second time after the
    # #list_files command has been processed.
    self.assertEqual(self.fake_ai.last_conversation.send_message_calls, 2)

    self.mock_list_files_command.Execute.assert_called_once()
    called_with_input = self.mock_list_files_command.Execute.call_args[0][0]
    self.assertIsInstance(called_with_input, CommandInput)
    self.assertEqual(called_with_input.command_name, "list_files")

  def test_run_loop_with_no_commands_in_response(self):
    """
    Tests that the loop sends an error back to the AI if it responds with no commands.
    """
    # 1. Setup: AI responds with text, then #done to terminate the loop.
    agent_loop = self._create_agent_loop_for_test(
        scripted_responses=["This is just conversational text.", "#done"])

    # 2. Run the agent loop.
    agent_loop.run()

    # 3. Assertions
    self.assertEqual(self.fake_ai.last_conversation.send_message_calls, 2)

    # The conversation history is now held in the agent_loop's conversation object.
    # [0] user: initial prompt
    # [1] assistant: "This is just conversational text."
    # [2] user: error message sent back to AI
    conversation = agent_loop.conversation
    self.assertEqual(len(conversation.messages), 4)
    last_message_to_ai = conversation.messages[2]
    self.assertEqual(last_message_to_ai.role, 'user')

    sections = last_message_to_ai.GetContentSections()
    self.assertEqual(len(sections), 1)
    self.assertEqual(sections[0].summary, "Error: No commands received")
    self.assertIn("Error: No commands found in response!",
                  sections[0].content[0])


if __name__ == '__main__':
  unittest.main()
