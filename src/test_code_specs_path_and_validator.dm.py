# DM validator:
#
# mypy $DMPATH && $PYTHON -m pytest $DMPATH
#
# See src/test-constraints.md for constraints that apply to these tests.

import aiofiles
import asyncio
import pathlib
import re
import tempfile
import unittest

from agent_command import Argument, ArgumentContentType, VariableMap, VariableName, VariableValueStr
from agent_loop_options import AgentLoopOptions, BaseAgentLoopFactory
from agent_workflow_options import AgentWorkflowOptions
from code_specs import FileExtension, MarkerChar, comment_string, get_markers
from code_specs_agent import prepare_command_registry, prepare_initial_message, run_agent_loop
from code_specs_path_and_validator import PathAndValidator
from code_specs_validator import Validator
from command_registry import CommandRegistry
from conversation import ConversationFactory, Conversation
from done_command import DoneCommand
from file_access_policy import FileAccessPolicy
from list_files_command import ListFilesCommand
from message import ContentSection, Message
from read_file_command import ReadFileCommand
from search_file_command import SearchFileCommand
from selection_manager import SelectionManager
from test_utils import FakeFileAccessPolicy, FakeConfirmationState, FakeConfirmationManager, FakeSelectionManager
from validation import ValidationResult


class TestPathAndValidator(unittest.IsolatedAsyncioTestCase):

  async def test_validate_fields_doesnt_raise_if_dm_path_is_a_valid_file_with_two_markers(
      self) -> None:
    pass  # {{🍄 PathAndValidator validate_fields Doesn't raise if `dm_path` is a valid file with two 🍄 markers.}}

  async def test_validate_fields_raises_value_error_if_dm_path_is_foo_py_lacks_the_dm_part(
      self) -> None:
    pass  # {{🍄 PathAndValidator validate_fields Raises ValueError if `dm_path` is "foo.py" (lacks the `.dm.` part).}}

  async def test_validate_fields_raises_value_error_if_dm_path_is_a_valid_file_with_no_markers(
      self) -> None:
    pass  # {{🍄 PathAndValidator validate_fields Raises ValueError if `dm_path` is a valid file with no 🍄 markers.}}

  async def test_validate_fields_raises_value_error_if_dm_path_contains_a_repeated_marker(
      self) -> None:
    pass  # {{🍄 PathAndValidator validate_fields Raises ValueError if `dm_path` contains a repeated 🍄 marker.}}

  def test_file_extension_for_dm_path_foobarquux_dm_py_returns_py(self) -> None:
    pass  # {{🍄 PathAndValidator file_extension For `dm_path` "foo/bar/quux.dm.py", returns "py"}}

  def test_output_path_if_dm_path_is_foobarquux_dm_py_returns_foobarquux_py(
      self) -> None:
    pass  # {{🍄 PathAndValidator output_path If `dm_path` is "foo/bar/quux.dm.py", returns "foo/bar/quux.py"}}

  def test_old_path_for_dm_path_foobar_dm_py_returns_foobar_old_py(
      self) -> None:
    pass  # {{🍄 PathAndValidator old_path For `dm_path` "foo/bar.dm.py", returns "foo/bar.old.py".}}

  async def test_overwrite_the_read_operation_is_async(self) -> None:
    pass  # {{🍄 PathAndValidator overwrite The read operation is async}}

  async def test_overwrite_the_write_operation_is_async(self) -> None:
    pass  # {{🍄 PathAndValidator overwrite The write operation is async}}

  async def test_overwrite_the_output_of_a_call_with_a_normal_dm_file_starts_with_the_do_not_edit_code_comment(
      self) -> None:
    pass  # {{🍄 PathAndValidator overwrite The output of a call with a normal dm file starts with the "DO NOT EDIT code comment}}

  async def test_overwrite_the_output_of_a_call_with_a_normal_dm_file_contains_a_copy_of_the_dm_file_starting_at_line_2_of_the_output(
      self) -> None:
    pass  # {{🍄 PathAndValidator overwrite The output of a call with a normal dm file contains a copy (of the dm file), starting at line 2 (of the output)}}


if __name__ == '__main__':
  unittest.main()
