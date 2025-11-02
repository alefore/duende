# DM validator:
#
# MYPYPATH=~/coding-agent/src mypy $DMPATH && $PYTHON -m pytest $DMPATH
#
# These tests have a few constraints:
#
# * Mock is NOT allowed in this code. These tests should let all the
#   dependencies  of CodeSpecsTestsSkeleton be used directly.
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
from collections import defaultdict
import os
import pathlib
import re
import shutil
import tempfile
from typing import Callable, Awaitable, Any
import unittest

from agent_command import Argument, AgentCommand, CommandOutput, CommandInput, AgentCommand, ArgumentContentType, VariableMap, VariableName, VariableValue, VariableValueStr
from agent_loop import AgentLoop, AgentLoopFactory
from agent_loop_options import AgentLoopOptions
from agent_workflow_options import AgentWorkflowOptions
from code_specs import PathAndValidator, Validator, prepare_command_registry, prepare_initial_message, run_agent_loop, ValidationResult, MarkerChar, MarkersOverlapError, MarkerName
from code_specs_tests_skeleton import CodeSpecsTestsSkeletonWorkflow, tests_skeleton_variable, MUSHROOM, HEDGEHOG, path_to_test_variable
from command_registry import CommandRegistry
from confirmation import ConfirmationManager, ConfirmationState
from conversation import Conversation, ConversationId, ConversationFactory, ConversationFactoryOptions
from conversation_state import ConversationState
from conversational_ai import ConversationalAI
from conversational_ai_test_utils import FakeConversationalAIConversation, FakeConversationalAI
from done_command import DoneCommand
from file_access_policy import FileAccessPolicy
from message import ContentSection, Message
from selection_manager import SelectionManager


class TestFileAccessPolicy(FileAccessPolicy):

  def allow_access(self, path: str) -> bool:
    return True  # Allow all access for testing


class TestConfirmationState(ConfirmationState):

  async def RequireConfirmation(self, conversation_id: int,
                                prompt: str) -> str | None:
    return None  # Always confirm


class TestConfirmationManager(ConfirmationManager):

  async def RequireConfirmation(self, conversation_id: ConversationId,
                                message: str) -> str | None:
    return None  # Always confirm for tests


class TestSelectionManager(SelectionManager):
  pass  # Default implementation is fine for now


class TestCodeSpecsTestsSkeletonWorkflow(unittest.IsolatedAsyncioTestCase):

  def setUp(self):
    self.conversation_factory = ConversationFactory(
        ConversationFactoryOptions())

  def done_message_with_path_to_test(self, path: pathlib.Path) -> Message:
    """Returns a Message calling `done` with `path_to_test_variable`."""
    raise NotImplementedError()  # {{🍄 done message with path to test}}

  def write_path_to_test_and_return_done_message(
      self, contents: str) -> tuple[Message, pathlib.Path]:
    """Returns a Message calling `done` with `path_to_test_variable`.

    The contents are written to a temporary file; its path is given to
    `path_to_test_variable` and returned. Clean-up of the temporary file is
    scheduled.

    The returned messages can be given directly to a FakeConversationalAI's list
    of messages. That implies that role should be "assistant".
    """
    raise NotImplementedError()  # {{🍄 write path to test}}

  def done_message_for_tests_skeleton(self, skeleton_content: str) -> Message:
    """Returns a Message calling `done` with `tests_skeleton_variable`.

    The returned messages can be given directly to a FakeConversationalAI's list
    of messages. That implies that role should be "assistant".
    """
    raise NotImplementedError()  # {{🍄 done message for skeleton}}

  def get_valid_contents_with_hedgehog_markers(self) -> str:
    """Returns a file (contents) with valid `"{{"+HEDGEHOG+prop+"}}"` markers.

    The file contains two different non-overlapping markers. Does not actually
    write the file, just returns text contents.
    """
    raise NotImplementedError()  # {{🍄 tmp file with markers}}

  async def build_workflow(
      self, scripted_messages: dict[str, list[Message]]
  ) -> CodeSpecsTestsSkeletonWorkflow:
    """Sets up a CodeSpecTestsSkeletonWorkflow with fake objects.

    Sets option skip_implicit_validation to True.
    """
    raise NotImplementedError()  # {{🍄 build workflow}}

  def filter_content_sections(
      self, predicate: Callable[[ContentSection],
                                bool]) -> list[ContentSection]:
    """Returns any content sections in any messages that match a predicate.

    Extracts the messages from self.conversation_factory."""
    raise NotImplementedError()  # {{🍄 filter content sections}}

  async def test_get_initial_parameters_only_path_to_test_variable_argument(
      self) -> None:
    pass  # {{🍄 The only done command argument given to `prepare_command_registry` is `path_to_test_variable`.}}

  async def test_initial_parameters_validator_fails_if_file_cant_be_read(
      self) -> None:
    pass  # {{🍄 Validation fails if the file can't be read.}}

  async def test_initial_parameters_validator_fails_if_no_hedgehog_markers(
      self) -> None:
    pass  # {{🍄 Validation fails if the file doesn't contain any HEDGEHOG markers (per `code_specs.get_markers`).}}

  async def test_initial_parameters_validator_succeeds_with_readable_file_and_hedgehog_markers(
      self) -> None:
    pass  # {{🍄 Validation succeeds if the file can be read and contains HEDGEHOG markers (per `code_specs.get_markers`).}}

  async def test_initial_parameters_validator_succeeds_with_repeated_hedgehog_markers(
      self) -> None:
    pass  # {{🍄 Validation succeeds if the file contains repeated (identical) HEDGEHOG markers (per `code_specs.get_markers`).}}

  async def test_initial_parameters_validator_only_requires_path_to_test_variable(
      self) -> None:
    pass  # {{🍄 Does not require any variables other than `path_to_test_variable`.}}

  async def test_prepare_tests_skeleton_only_tests_skeleton_variable_argument(
      self) -> None:
    pass  # {{🍄 The only done command argument given to `prepare_command_registry` in `_prepare_tests_skeleton` is `tests_skeleton_variable`.}}

  async def test_prepare_tests_skeleton_writes_to_test_file_after_validation(
      self) -> None:
    pass  # {{🍄 After validating that the skeleton contains all tests, writes them to a `tests_…` file (e.g., when `input` is `src/foo.py`, writes `src/test_foo.py`).}}

  async def test_prepare_tests_skeleton_input_passed_as_relevant_file(
      self) -> None:
    pass  # {{🍄 `input` is passed as a relevant file to `prepare_initial_message`.}}

  async def test_tests_skeleton_validator_fails_if_markers_rejected_by_get_markers(
      self) -> None:
    pass  # {{🍄 Fails if the set of markers given in tests_skeleton_variable is rejected by `code_spec.get_markers(MUSHROOM, output)`.}}

  async def test_tests_skeleton_validator_fails_if_identical_mushroom_marker_repeated(
      self) -> None:
    pass  # {{🍄 Fails if an identical marker (in the value of `tests_skeleton_variable`) is repeated (more than one location, per `code_spec.get_markers(MUSHROOM, output)`).}}

  async def test_tests_skeleton_validator_fails_if_marker_count_mismatch(
      self) -> None:
    pass  # {{🍄 Fails if the number of HEDGEHOG markers in the input isn't exactly the same as the number of MUSHROOM markers in the output.}}

  async def test_tests_skeleton_validator_only_requires_tests_skeleton_variable(
      self) -> None:
    pass  # {{🍄 Does not require any variables beyond `tests_skeleton_variable`.}}


if __name__ == '__main__':
  unittest.main()
