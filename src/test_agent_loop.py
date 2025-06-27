import unittest
from unittest.mock import MagicMock

from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax
from agent_loop import AgentLoop
from agent_loop_options import AgentLoopOptions
from command_registry import CommandRegistry
from conversation import Conversation, ConversationFactory, Message, ContentSection
from conversational_ai_test_utils import FakeConversationalAI
from file_access_policy import FileAccessPolicy, CurrentDirectoryFileAccessPolicy


class TestAgentLoop(unittest.TestCase):
  """Tests the main AgentLoop execution flow."""

  def setUp(self):
    """Set up common stateless mocks for all tests."""
    self.mock_list_files_command = MagicMock(spec=AgentCommand)
    self.mock_list_files_command.Name.return_value = "list_files"
    self.mock_list_files_command.Aliases.return_value = set()
    self.mock_list_files_command.Syntax.return_value = CommandSyntax(
        multiline=None,
        required=[],
        optional=[],
        repeatable_final=None,
    )
    self.mock_list_files_command.Execute.return_value = CommandOutput(
        output=["src/agent_loop.py"], errors=[], summary="Listed 1 file.")

    self.registry = CommandRegistry()
    self.registry.Register(self.mock_list_files_command)

    self.mock_confirmation_state = MagicMock()
    self.mock_confirmation_state.RequireConfirmation.return_value = ""

    self.conv_factory = ConversationFactory()

    self.file_access_policy = CurrentDirectoryFileAccessPolicy()

  def _run_agent_loop_for_test(self,
                               scripted_responses: list[str]) -> Conversation:
    """Creates and runs an AgentLoop instance, returning the conversation."""
    self.fake_ai = FakeConversationalAI(scripted_responses=scripted_responses)
    conversation = Conversation(unique_id=0, name="test-name")

    options = AgentLoopOptions(
        task_prompt_content=["Test task"],
        conversation_factory=self.conv_factory,
        conversation_path="/tmp/test_conversation.json",
        model="test-model",
        conversation=conversation,
        start_message=Message(
            role='user',
            content_sections=[ContentSection(content=["Test Task"])]),
        commands_registry=self.registry,
        confirmation_state=self.mock_confirmation_state,
        file_access_policy=self.file_access_policy,
        conversational_ai=self.fake_ai,
        confirm_done=False,
        skip_implicit_validation=True,
    )
    agent_loop = AgentLoop(options)
    agent_loop.run()
    return conversation

  def test_run_loop_with_simple_command_and_done(self):
    """
    Tests a simple interaction where the AI issues one command and then #done.
    """
    # 1. Setup and run the agent loop.
    conversation = self._run_agent_loop_for_test(
        scripted_responses=["#list_files", "#done"])

    # 2. Assertions: Verify the loop behaved as expected.
    # The conversation should have 4 messages:
    # 1. User: Initial task
    # 2. Assistant: #list_files
    # 3. User: output of list_files
    # 4. Assistant: #done
    self.assertEqual(len(conversation.messages), 4)

    # Verify that the output of the command was sent to the AI.
    command_output_message = conversation.messages[2]
    self.assertEqual(command_output_message.role, 'user')
    sections = command_output_message.GetContentSections()
    self.assertEqual(len(sections), 1)
    self.assertEqual(sections[0].summary, "Listed 1 file.")
    self.assertEqual(sections[0].content, ["src/agent_loop.py"])

    self.mock_list_files_command.Execute.assert_called_once()
    called_with_input = self.mock_list_files_command.Execute.call_args[0][0]
    self.assertIsInstance(called_with_input, CommandInput)
    self.assertEqual(called_with_input.command_name, "list_files")

  def test_run_loop_with_no_commands_in_response(self):
    """
    Tests that the loop sends an error back to the AI if it responds with no commands.
    """
    # 1. Setup and run the agent loop.
    conversation = self._run_agent_loop_for_test(
        scripted_responses=["This is just conversational text.", "#done"])

    # 2. Assertions
    # The conversation should have 4 messages:
    # 1. User: Initial task
    # 2. Assistant: conversational text
    # 3. User: Error message
    # 4. Assistant: #done
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
