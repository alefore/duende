import os
import unittest
from unittest.mock import MagicMock, call, patch
from typing import Dict, List, Union
import glob
import logging

import review_utils
from agent_command import (AgentCommand, CommandInput, CommandOutput,
                           CommandSyntax, Argument, ArgumentContentType)
from agent_loop import AgentLoop
from agent_loop_options import AgentLoopOptions
from command_registry import CommandRegistry
from conversation import Conversation, ConversationFactory, Message, ContentSection, ConversationFactoryOptions
from conversational_ai_test_utils import FakeConversationalAI
from done_command import DoneCommand
from file_access_policy import FileAccessPolicy, CurrentDirectoryFileAccessPolicy
# Import real commands
from review_commands import AcceptChange, RejectChange


class TestAgentLoop(unittest.TestCase):
  """Tests the main AgentLoop execution flow."""

  def setUp(self):
    """Set up common stateless mocks for all tests."""
    self.mock_list_files_command = MagicMock(spec=AgentCommand)
    self.mock_list_files_command.Name.return_value = "list_files"
    self.mock_list_files_command.Syntax.return_value = CommandSyntax(
        name="list_files",
        description="Lists all files in the given directories.",
        arguments=[],
    )
    self.mock_list_files_command.run.return_value = CommandOutput(
        command_name="list_files",
        output="src/agent_loop.py",
        errors="",
        summary="Listed 1 file.")

    self.mock_read_file_command = MagicMock(spec=AgentCommand)
    self.mock_read_file_command.Name.return_value = "read_file"
    self.mock_read_file_command.Syntax.return_value = CommandSyntax(
        name="read_file",
        description="Reads the contents of a file.",
        arguments=[
            Argument(
                name='path',
                # Technically, it would be more correct to use PATH_INPUT;
                # but then we'd have to create the file (or else AgentLoop will
                # register an error).
                arg_type=ArgumentContentType.PATH_INPUT_OUTPUT,
                description='The path of the file to be read.',
                required=True)
        ],
    )
    self.mock_read_file_command.run.return_value = CommandOutput(
        command_name="read_file",
        output="file content",
        errors="",
        summary="Read 1 file.")

    self.mock_write_file_command = MagicMock(spec=AgentCommand)
    self.mock_write_file_command.Name.return_value = "write_file"
    self.mock_write_file_command.Syntax.return_value = CommandSyntax(
        name="write_file",
        description="Writes the given content to a specified file.",
        arguments=[
            Argument(
                name='path',
                arg_type=ArgumentContentType.PATH_INPUT_OUTPUT,
                description='The file path to write the content to.',
                required=True),
            Argument(
                name='content',
                arg_type=ArgumentContentType.STRING,
                description='The content to write.',
                required=True),
        ],
    )
    self.mock_write_file_command.run.return_value = CommandOutput(
        command_name="write_file",
        output="",
        errors="",
        summary="Wrote to file.")

    self.registry = CommandRegistry()
    self.registry.Register(self.mock_list_files_command)
    self.registry.Register(self.mock_read_file_command)
    self.registry.Register(self.mock_write_file_command)
    self.registry.Register(DoneCommand())

    # Dummy callback for the real AcceptChange and RejectChange commands
    # These commands are not expected to be run by the main agent in this test setup
    # but they need to be registered with a valid constructor.
    def dummy_review_callback(command_output):
      pass

    self.registry.Register(AcceptChange(dummy_review_callback))
    self.registry.Register(RejectChange(dummy_review_callback))

    self.mock_confirmation_state = MagicMock()
    self.mock_confirmation_state.RequireConfirmation.return_value = ""

    self.conv_factory = ConversationFactory(
        ConversationFactoryOptions(command_registry=self.registry))

    self.file_access_policy = CurrentDirectoryFileAccessPolicy()

  def tearDown(self):
    """Clean up any created files after each test."""
    conv_path = "/tmp/test_conversation.json"
    if os.path.exists(conv_path):
      os.remove(conv_path)

    for review_file in glob.glob('/tmp/test_conversation.*.review.json'):
      if os.path.exists(review_file):
        os.remove(review_file)

  def _run_agent_loop_for_test(self,
                               scripted_responses: Dict[str, List[Message]],
                               confirm_done: bool = False,
                               do_review: bool = False) -> List[Message]:
    """Creates and runs an AgentLoop instance, returning the conversation."""
    self.fake_ai = FakeConversationalAI(scripted_responses=scripted_responses)
    conversation = Conversation(
        unique_id=0,
        name="test-name",
        path="/tmp/test_conversation.json",
        command_registry=self.registry)

    options = AgentLoopOptions(
        task_prompt_content="Test task",
        conversation_factory=self.conv_factory,
        conversation=conversation,
        start_message=Message(
            role='user',
            content_sections=[ContentSection(content="Test Task")]),
        commands_registry=self.registry,
        confirmation_state=self.mock_confirmation_state,
        file_access_policy=self.file_access_policy,
        conversational_ai=self.fake_ai,
        confirm_done=confirm_done,
        do_review=do_review,
        skip_implicit_validation=True,
    )
    agent_loop = AgentLoop(options)
    agent_loop.run()
    return conversation.messages

  def test_run_loop_with_simple_command_and_done(self):
    """
    Tests a simple interaction where the AI issues one command and then #done.
    """
    # 1. Setup and run the agent loop.
    messages = self._run_agent_loop_for_test({
        "test-name": [
            Message(
                role='assistant',
                content_sections=[
                    ContentSection(
                        command=CommandInput(command_name="list_files"),
                        content="")
                ]),
            Message(
                role='assistant',
                content_sections=[
                    ContentSection(
                        command=CommandInput(command_name="done"), content="")
                ]),
        ]
    })

    # 2. Assertions: Verify the loop behaved as expected.
    # The conversation should have 4 messages:
    # 1. User: Initial task
    # 2. Assistant: #list_files
    # 3. User: output of list_files
    # 4. Assistant: #done
    self.assertEqual(len(messages), 4)

    # Verify that the output of the command was sent to the AI.
    command_output_message = messages[2]
    self.assertEqual(command_output_message.role, 'user')
    sections = command_output_message.GetContentSections()
    self.assertEqual(len(sections), 1)
    self.assertEqual(sections[0].summary, "Listed 1 file.")
    self.assertEqual(
        sections[0].command_output,
        CommandOutput(
            command_name="list_files",
            output="src/agent_loop.py",
            errors="",
            summary="Listed 1 file."))

    self.mock_list_files_command.run.assert_called_once_with({})

  def test_run_loop_with_no_commands_in_response(self):
    """
    Tests that the loop sends an error back to the AI if it responds with no commands.
    """
    # 1. Setup and run the agent loop.
    messages = self._run_agent_loop_for_test({
        "test-name": [
            Message(
                role='assistant',
                content_sections=[
                    ContentSection(content="This is just conversational text.")
                ]),
            Message(
                role='assistant',
                content_sections=[
                    ContentSection(
                        command=CommandInput(command_name="done"), content="")
                ]),
        ]
    })

    # The conversation should have 4 messages:
    # 0. User: Initial task
    # 1. Assistant: conversational text
    # 2. User: Empty.
    # 3. Assistant: #done
    self.assertEqual(len(messages), 4)

    last_message_to_ai = messages[2]
    self.assertEqual(last_message_to_ai.role, 'user')
    self.assertEqual(len(messages[2].GetContentSections()), 0)  # Empty!

    self.assertEqual(len(messages[3].GetContentSections()), 1)
    self.assertEqual(messages[3].GetContentSections()[0].command.command_name,
                     "done")

  def test_run_loop_with_multiple_commands(self):
    """
    Tests that the loop correctly executes multiple commands from one response.
    """
    # 1. Setup and run the agent loop.
    # The scripted response contains two command lines in a single message.
    messages = self._run_agent_loop_for_test({
        "test-name": [
            Message(
                role='assistant',
                content_sections=[
                    ContentSection(
                        command=CommandInput(command_name="list_files"),
                        content=""),
                    ContentSection(
                        command=CommandInput(
                            command_name="read_file", args={'path': 'foo.py'}),
                        content="")
                ]),
            Message(
                role='assistant',
                content_sections=[
                    ContentSection(
                        command=CommandInput(command_name="done"), content="")
                ]),
        ]
    })

    # 2. Assertions
    self.mock_list_files_command.run.assert_called_once_with({})
    self.mock_read_file_command.run.assert_called_once_with({'path': 'foo.py'})

    # The conversation should have 4 messages:
    # 1. User: Initial task
    # 2. Assistant: #list_files, #read_file
    # 3. User: output of both commands
    # 4. Assistant: #done
    self.assertEqual(len(messages), 4)
    output_message = messages[2]
    self.assertEqual(output_message.role, 'user')
    sections = output_message.GetContentSections()
    self.assertEqual(len(sections), 2)
    self.assertEqual(sections[0].summary, "Listed 1 file.")
    self.assertEqual(sections[1].summary, "Read 1 file.")

  def test_done_confirmation_with_rejection(self):
    """
    Tests that the loop continues if the user rejects the #done command.
    """
    # 1. Setup mocks and run the loop
    # First call to confirmation returns guidance, second returns empty to terminate.
    self.mock_confirmation_state.RequireConfirmation.side_effect = [
        "You are not done, please list files.", ""
    ]
    messages = self._run_agent_loop_for_test(
        {
            "test-name": [
                Message(
                    role='assistant',
                    content_sections=[
                        ContentSection(
                            command=CommandInput(command_name="done"),
                            content="")
                    ]),
                Message(
                    role='assistant',
                    content_sections=[
                        ContentSection(
                            command=CommandInput(command_name="list_files"),
                            content="")
                    ]),
                Message(
                    role='assistant',
                    content_sections=[
                        ContentSection(
                            command=CommandInput(command_name="done"),
                            content="")
                    ]),
            ]
        },
        confirm_done=True)

    # 2. Assertions
    # The conversation should have 6 messages:
    # 1. User: Initial task
    # 2. Assistant: #done (rejected)
    # 3. User: Human guidance "You are not done..."
    # 4. Assistant: #list_files
    # 5. User: output of list_files
    # 6. Assistant: #done (accepted)
    self.assertEqual(len(messages), 6)

    # Check that confirmation was requested twice
    self.assertEqual(
        self.mock_confirmation_state.RequireConfirmation.call_count, 2)

    # Check that human guidance was sent to AI
    guidance_message = messages[2]
    self.assertEqual(guidance_message.role, 'user')
    sections = guidance_message.GetContentSections()
    self.assertEqual(len(sections), 2)
    self.assertEqual(sections[0].summary, "Task completed.")
    self.assertEqual(sections[0].content, "")
    self.assertEqual(sections[0].command_output.task_done, True)
    self.assertEqual(sections[1].summary, "Human decision to continue")
    self.assertIn("You are not done", sections[1].content)

    # Check that the next command was executed after guidance
    self.mock_list_files_command.run.assert_called_once_with({})

  def test_do_review_parallel(self):
    """Tests that do_review can trigger three parallel reviews."""
    main_conv_name = "test-name"
    review_0_conv_name = "AI Review (review_0): test-name"
    review_1_conv_name = "AI Review (review_1): test-name"
    review_2_conv_name = "AI Review (review_2): test-name"

    scripted_responses = {
        main_conv_name: [
            Message(
                role='assistant',
                content_sections=[
                    ContentSection(
                        command=CommandInput(
                            command_name="write_file",
                            args={
                                'path': 'a.py',
                                'content': 'a'
                            }),
                        content="")
                ]),
            Message(
                role='assistant',
                content_sections=[
                    ContentSection(
                        command=CommandInput(command_name="done"), content="")
                ]),
            Message(  # Second done command, after review feedback
                role='assistant',
                content_sections=[
                    ContentSection(
                        command=CommandInput(command_name="done"), content="")
                ]),
        ],
        review_0_conv_name: [
            Message(
                role='assistant',
                content_sections=[
                    ContentSection(
                        command=CommandInput(
                            command_name="reject_change",
                            args={'reason': 'Feedback from review 0.'}),
                        content="")
                ]),
        ],
        review_1_conv_name: [
            Message(
                role='assistant',
                content_sections=[
                    ContentSection(
                        command=CommandInput(
                            command_name="reject_change",
                            args={'reason': 'Feedback from review 1.'}),
                        content="")
                ]),
        ],
        review_2_conv_name: [
            Message(
                role='assistant',
                content_sections=[
                    ContentSection(
                        command=CommandInput(
                            command_name="accept_change",
                            args={'reason': 'Accepted review 2.'}),
                        content="")
                ]),
        ],
    }
    with patch('glob.glob') as mock_glob, \
         patch('review_utils.ReadReviewPromptFile') as mock_read_prompt, \
         patch('review_utils.GetGitDiffContent') as mock_get_diff:

      mock_glob.return_value = [
          'agent/review/review_0.txt', 'agent/review/review_1.txt',
          'agent/review/review_2.txt'
      ]
      mock_read_prompt.side_effect = [
          "Review prompt 0.",
          "Review prompt 1.",
          "Review prompt 2.",
      ]
      mock_get_diff.side_effect = [
          '--- a/a.py\n',  # Main agent's change, triggers reviews
          '',  # After feedback, agent issues #done, no new changes
      ]

      messages = self._run_agent_loop_for_test(
          scripted_responses=scripted_responses, do_review=True)

    logging.info([m.Serialize() for m in messages])
    # Diff happens twice, once for each Done command (the 2nd time to detect
    # that no review is needed).
    self.assertEqual(mock_get_diff.call_count, 2)
    mock_glob.assert_called_once_with('agent/review/*.txt')
    self.assertEqual(mock_read_prompt.call_count, 3)
    # The conversation should have 6 messages: (initial user, assistant write_file, user empty, assistant done, user review feedback, assistant done)
    self.assertEqual(len(messages), 6)

    feedback_message = messages[4]
    self.assertEqual(feedback_message.role, 'user')
    sections = feedback_message.GetContentSections()
    # Expect: 1 done + 2 rejection messages + 1 instruction message.
    self.assertEqual(len(sections), 4)

    instruction_sections = [
        s for s in sections if s.summary == "Instructions about review results"
    ]
    rejection_sections = [
        s for s in sections if s.summary.startswith("Review rejection from")
    ]

    self.assertEqual(len(instruction_sections), 1)
    self.assertEqual(len(rejection_sections), 2)

    summaries = [s.summary for s in rejection_sections]
    self.assertTrue(any("from review_0" in s for s in summaries))
    self.assertTrue(any("from review_1" in s for s in summaries))
    self.assertFalse(any("from review_2" in s for s in summaries))

    contents = [s.content for s in sections]
    self.assertTrue(
        any("Evaluator review_0 found issues with your change:\n\nChange rejected."
            in s for s in contents))
    self.assertTrue(
        any("Evaluator review_1 found issues with your change:\n\nChange rejected."
            in s for s in contents))
    self.assertFalse(any("Evaluator review_2" in s for s in contents))
    self.assertTrue(
        any("Please consider addressing the following issues that caused the evaluatores to reject your change and try again."
            in s for s in contents))


if __name__ == '__main__':
  unittest.main()
