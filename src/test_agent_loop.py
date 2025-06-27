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

  def test_run_loop_with_simple_command_and_done(self):
    """
        Tests a simple interaction where the AI issues one command and then #done.
        """
    # 1. Setup: Define the AI's scripted responses.
    script = ["#list_files", "#done"]
    fake_ai = FakeConversationalAI(scripted_responses=script)

    # 2. Setup: Mock the command that the AI will call.
    # FIX: Syntax() must return a structured object, not a string.
    mock_syntax = MagicMock(spec=CommandSyntax)
    mock_syntax.multiline = None
    mock_syntax.required = []
    mock_syntax.optional = []
    mock_syntax.repeatable_final = None

    mock_list_files_command = MagicMock(spec=AgentCommand)
    mock_list_files_command.Name.return_value = "list_files"
    mock_list_files_command.Aliases.return_value = set()
    mock_list_files_command.Syntax.return_value = mock_syntax
    mock_list_files_command.Execute.return_value = CommandOutput(
        output=["src/agent_loop.py"], errors=[], summary="Listed 1 file.")

    registry = CommandRegistry()
    registry.Register(mock_list_files_command)

    # 3. Setup: Mock other dependencies for AgentLoopOptions.
    mock_confirmation_state = MagicMock()
    mock_confirmation_state.RequireConfirmation.return_value = ""
    mock_conv_factory = MagicMock(spec=ConversationFactory)
    mock_file_access_policy = MagicMock(spec=FileAccessPolicy)

    # 4. Setup: Create AgentLoopOptions with all required fields.
    options = AgentLoopOptions(
        task_prompt_content=["Test task"],
        conversation_factory=mock_conv_factory,
        conversation_path="/tmp/test_conversation.json",
        model="test-model",
        conversation=Conversation(unique_id="test-id", name="test-name"),
        start_message=Message(
            role='user',
            content_sections=[ContentSection(content=["Test Task"])]),
        commands_registry=registry,
        confirmation_state=mock_confirmation_state,
        file_access_policy=mock_file_access_policy,
        conversational_ai=fake_ai,
        confirm_done=False,
        skip_implicit_validation=True,
    )

    # 5. Run the agent loop.
    agent_loop = AgentLoop(options)
    agent_loop.run()

    # 6. Assertions: Verify the loop behaved as expected.
    self.assertIsNotNone(fake_ai.last_conversation)
    self.assertEqual(fake_ai.last_conversation.send_message_calls, 2)

    mock_list_files_command.Execute.assert_called_once()
    called_with_input = mock_list_files_command.Execute.call_args[0][0]
    self.assertIsInstance(called_with_input, CommandInput)
    self.assertEqual(called_with_input.command_name, "list_files")


if __name__ == '__main__':
  unittest.main()
