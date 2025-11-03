# DM validator:
#
# MYPYPATH=~/coding-agent/src mypy $DMPATH && $PYTHON -m pytest $DMPATH
#
# These tests have a few constraints:
#
# * Mock is NOT allowed in this code. These tests should let all the
#   dependencies of code_specs_agent be used directly.
#   The only exception is mocking parts of aiofiles in tests that need to
#   validate that operations are asynchronous.
#
# * These tests are not allowed to implement BaseAgentLoop directly; instead,
#   they must always use AgentLoop and AgentLoopFactory.
#
# * These tests must NOT subclass AgentLoop nor AgentLoopFactory, nor mock any
#   of their methods.
#
# * These tests must NOT contain the 🍄 character anywhere (in order to avoid
#   possible clashes with Duende, since that is already interpreting markers).
#
# * If they need to get a conversation, these tests must get it from the
#   self.conversation_factory. They must NOT get it from the conversational_ai.

import aiofiles
import asyncio
import pathlib
import tempfile
import unittest
from typing import Awaitable, Callable
from unittest import mock

from agent_command import Argument, ArgumentContentType, VariableMap, VariableName, VariableValueStr
from agent_loop_options import AgentLoopOptions, BaseAgentLoopFactory
from agent_workflow_options import AgentWorkflowOptions
from code_specs_agent import prepare_command_registry, prepare_initial_message, run_agent_loop
from command_registry import CommandRegistry
from conversation import ConversationFactory, ConversationFactoryOptions, Conversation
from conversational_ai_test_utils import FakeConversationalAIConversation, FakeConversationalAI
from done_command import DoneCommand, DoneValuesValidator
from file_access_policy import FileAccessPolicy
from list_files_command import ListFilesCommand
from message import ContentSection, Message
from read_file_command import ReadFileCommand
from search_file_command import SearchFileCommand
from selection_manager import SelectionManager
from test_utils import FakeFileAccessPolicy, FakeConfirmationState, FakeConfirmationManager, FakeSelectionManager
from validation import ValidationResult


class TestCodeSpecsAgent(unittest.IsolatedAsyncioTestCase):

  async def test_prepare_initial_message_relevant_files_read_asynchronously(
      self) -> None:
    pass  # {{🍄 prepare_initial_message: `relevant_files` are read asynchronously.}}

  async def test_prepare_initial_message_output_contains_start_message_content_as_first_section(
      self) -> None:
    pass  # {{🍄 prepare_initial_message: The output contains `start_message_content` as its first section.}}

  async def test_prepare_initial_message_if_relevant_files_empty_output_has_just_one_section(
      self) -> None:
    pass  # {{🍄 prepare_initial_message: If `relevant_files` is empty, the output has just one section.}}

  async def test_prepare_initial_message_if_relevant_file_cant_be_read_exception_bubbles_up(
      self) -> None:
    pass  # {{🍄 prepare_initial_message: If a relevant file can't be read, raises an exception (or, rather, lets the underlying exception bubble up, doesn't catch it).}}

  async def test_prepare_initial_message_content_section_for_each_relevant_file_with_path_and_contents(
      self) -> None:
    pass  # {{🍄 prepare_initial_message: There is a content section in the start message given to the AgentLoop for each entry in `relevant_files`. It starts with a line "File '{path}' follows:" (with the corresponding path) and includes the entire contents of the file.}}

  async def test_prepare_command_registry_has_expected_agent_commands(
      self) -> None:
    pass  # {{🍄 prepare_command_registry: The command registry given has exactly these agent commands: ReadFileCommand(…), ListFilesCommand(…), SearchFileCommand(…), done_command}}

  async def test_run_agent_loop_returns_variable_map_from_done_command(
      self) -> None:
    pass  # {{🍄 run_agent_loop: Returns the `VariableMap` with all the values given to `DoneCommand`.}}

  async def test_run_agent_loop_conversation_has_given_name(self) -> None:
    pass  # {{🍄 run_agent_loop: The conversation started has name `conversation_name`.}}

  async def test_run_agent_loop_start_message_is_initial_message(self) -> None:
    pass  # {{🍄 run_agent_loop: `start_message` is given as the initial message.}}


if __name__ == '__main__':
  unittest.main()
