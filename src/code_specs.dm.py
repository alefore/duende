"""Supporting logic for DM-related workflows.md."""

import aiofiles
import asyncio
import dataclasses
import logging
import pathlib
import re
import os
import shutil
import subprocess
import tempfile
from typing import Awaitable, Callable, NamedTuple, NewType, Pattern, Sequence

from agent_command import Argument, ArgumentContentType, VariableMap, VariableName, VariableValue
from agent_loop_options import AgentLoopOptions
from agent_workflow_options import AgentWorkflowOptions
from command_registry import CommandRegistry
from done_command import DoneCommand, DoneValuesValidator
from file_access_policy import FileAccessPolicy
from list_files_command import ListFilesCommand
from message import Message, ContentSection
from read_file_command import ReadFileCommand
from search_file_command import SearchFileCommand
from validation import ValidationResult
from write_file_command import WriteFileCommand

# A FileExtension like "py" or "html".
FileExtension = NewType("FileExtension", str)

MarkerChar = NewType("MarkerChar", str)


def comment_string(file_extension: FileExtension, input: str) -> str:
  """Turns `input` into a valid code comment based on `path`'s extension.

  Supported extensions: py, sh, cc, h, js, ts, java, html, css

  {{🦔 "py" and "foo bar" returns "# foo bar"}}
  {{🦔 "html" and "my test" returns "<!-- my test -->}}
  """
  #  {{🍄 get comment char}}
  raise ValueError(f"Unknown file extension: {file_extension}")


def marker_pattern(char: str) -> re.Pattern:
  """Returns a regex to search for code lines with DM markers.

  A DM marker has the form "{{" + char + an arbitrary name (which may
  contain spaces, such as "    test method foo  ") + "}}". The first match group
  captures the name, with any leading/trailing spaces stripped away. Must be
  applied to individual lines (i.e., not to the whole file).

  {{🦔 Matches "      {{X foo}}" (with char "X")}}
  {{🦔 Matches "  return Foo()   #  {{X bar}} blah" (char == "X")}}
  {{🦔 Doesn't match with space before char: "{{ X foo}}" (char == "X")}}
  {{🦔 Doesn't match random line "  if (kobolds_found) {"}}
  """
  return re.compile(r'...')  #  {{🍄 marker pattern}}


class MarkerName(NamedTuple):
  char: MarkerChar
  name: str


class MarkerImplementation:

  def __init__(self, name: MarkerName, value: str,
               file_extension: FileExtension) -> None:
    """Sets _name, _value, _file_extension from inputs.

    The value is the full implementation.

    Raises:
      ValueError unless `value` starts and ends with appropriate `✨` comments.
        Per doc/code-specs.md, these comments may contain leading whitespaces.
    """
    raise NotImplementedError()  # {{🍄 marker implementation constructor}}

  # {{🦔 A call to MarkerImplementation.name returns the correct name}}
  # {{🦔 A call to MarkerImplementation.value returns the correct value}}
  # {{🍄 `name` and `value` getters}}

  async def save(self, path: pathlib.Path) -> None:
    """Rewrites `path`, storing our implementation.

    {{🦔 The read operation is async}}
    {{🦔 The write operation is async}}
    {{🦔 Successfully expands a marker in a file with a single marker}}
    {{🦔 Successfully expands the correct marker in a file with ten markers}}
    {{🦔 The value is stored literally, without adding any leading spaces}}
    {{🦔 Raises ValueError if the marker doesn't occur in `path`}}
    {{🦔 Raises ValueError if the marker occurs twice in `path`}}
    {{🦔 Raises FileNotFound if the file does not exist}}
    {{🦔 Raises ValueError if `path` contains a ".dm." part}}

    Raises:
      ValueError if `path` has a `.dm.` part. DM files themselves should never
      be updated.
    """
    raise NotImplementedError()  # {{🍄 marker implementation save}}


@dataclasses.dataclass(frozen=True)
class Validator:
  """A shell command that validates contents of a file.

  The command receives the path through $DMPATH. It should be able to validate
  copies on /tmp of input files (i.e., must not assume that it is always run in
  some particular directory).

  Validation is successful if the command exits with 0. If the DM file being
  implemented contains unit tests, this typically just runs it.
  """
  command: str

  def __post_init__(self):
    """Raises ValueError if the command doesn't include the string "DMPATH".

    {{🦔 Raises for incorrect string: "MYPYPATH=foo mypy {path}"}}
    {{🦔 Raises for incorrect string: "MYPYPATH=foo mypy $DM_PATH"}}
    {{🦔 Doesn't raise for "MYPYPATH=foo mypy $DMPATH"}}
    """
    raise NotImplementedError()  # {{🍄 validator post init}}

  async def validate_path(self, dm_path: pathlib.Path) -> ValidationResult:
    """Runs `command` on `dm_path` to validate it.

    {{🦔 Returns failure for "false # $DMPATH"}}
    {{🦔 Returns success for "true # $DMPATH"}}
    {{🦔 Correctly passes `dm_path` through the `DMPATH` env variable}}
    {{🦔 Command `TEST=foo sh -c 'test "$TEST" = "foo"' # $DMPATH` succeeds.
         This validates that we can actually processes shell syntax.}}
    """
    env = os.environ.copy()
    env['DMPATH'] = str(dm_path)
    raise NotImplementedError()  # {{🍄 validator validate}}

  async def validate_marker_implementation(
      self, source: pathlib.Path,
      implementation: MarkerImplementation) -> ValidationResult:
    """Validates the implementation of a marker on a copy of `source`.

    {{🦔 The read operation is async}}
    {{🦔 The write operation is async}}
    {{🦔 Does not modify `source`}}
    {{🦔 Returns success when the implementation is correct}}
    {{🦔 Returns failure when the implementation is invalid}}
    """
    raise NotImplementedError()  # {{🍄 implement validator}}


async def get_markers(char: MarkerChar, path: pathlib.Path) -> list[MarkerName]:
  """Returns all markers in `path` in appearance order.

  {{🦔 Reads `path` asynchronously}}
  {{🦔 Returns [] for an empty file}}
  {{🦔 Raises FileNotFound for a non-existent file}}
  {{🦔 Returns [] for a file with 5 lines but no markers}}
  {{🦔 Correctly returns a marker in a file with just 1 marker}}
  {{🦔 Spaces are correctly removed from a marker named "  foo bar  "}}
  {{🦔 Returns all markers in a file with ten markers}}
  {{🦔 The order of markers returned in a file with ten markers is correct}}
  {{🦔 Raises ValueError for a file with a repeated marker (among others)}}
  {{🦔 A file with three repeated markers raises ValueError; the description
      mentions all markers explicitly}}

  Raises:
      ValueError if the file contains repeated markers.
  """
  raise NotImplementedError()  # {{🍄 list markers}}


@dataclasses.dataclass(frozen=True)
class PathAndValidator:
  """An immutable container for a DM file path and a validator."""
  dm_path: pathlib.Path
  validator: Validator

  async def validate_fields(self):
    """Validates fields, conditionally raising ValueError.

    {{🦔 Doesn't raise if `dm_path` is a valid file with two markers}}
    {{🦔 Raises ValueError if `dm_path` is "foo.py"}}
    {{🦔 Raises ValueError if `dm_path` is a valid Python file with no markers}}
    {{🦔 Raises ValueError if `dm_path` contains a repeated marker}}

    We can't use `__post_init__` because we want `async` validation.
    """
    # {{🍄 PathAndValidator validate fields}}

  def output_path(self) -> pathlib.Path:
    """Returns `dm_path` without the `.dm` part.

    {{🦔 If `dm_path` is "foo/bar/quux.dm.py", returns "foo/bar/quux.py"}}
    """
    raise NotImplementedError()  # {{🍄 PathAndValidator output path}}

  async def overwrite(self, target: pathlib.Path) -> None:
    """Copies `dm_path`'s contents to `target` (overwriting it).

    The contents of the new file are:

    * A line with the comment:
      "DO NOT EDIT. This file is automatically generated by Duende."
    * The entire (unmodified) contents of `dm_path`.

    {{🦔 The read operation is async}}
    {{🦔 The write operation is async}}
    {{🦔 The output of a call with a normal dm file starts with the "DO NOT EDIT
         code comment}}
    {{🦔 The output of a call with a normal dm file contains a copy (of the dm
         file), starting at line 2 (of the output)}}
    """
    raise NotImplementedError()  # {{🍄 overwrite}}


async def prepare_initial_message(
    start_message_content: str, relevant_files: list[pathlib.Path]) -> Message:
  """Creates the first message for an AgentLoop conversation.

  {{🦔 `relevant_files` are read asynchronously}}
  {{🦔 The output contains `start_message_content` in its first section}}
  {{🦔 If `relevant_files` is empty, the output has just one section}}
  {{🦔 There is a content section in the start message given to the AgentLoop
       for each entries in `relevant_files`. It starts with a line
       "File "{path}" follows:" (with the corresponding path) and includes
       the entire contents of the file.}}
  """
  raise NotImplementedError()  # {{🍄 prepare initial message}}


async def prepare_command_registry(
    done_validator_callback: Callable[[VariableMap],
                                      Awaitable[ValidationResult]],
    file_access_policy: FileAccessPolicy) -> CommandRegistry:
  """Creates a command registry suitable for run_agent_loop.

  {{🦔 The command registry given has exactly these agent commands:
       ReadFileCommand(…), ListFilesCommand(…), SearchFileCommand(…),
       done_command}}
  """
  raise NotImplementedError()  # {{🍄 prepare command registry}}


async def run_agent_loop(workflow_options: AgentWorkflowOptions,
                         conversation_name: str, start_message: Message,
                         command_registry: CommandRegistry) -> VariableMap:
  """Creates and runs a BaseAgentLoop.

  {{🦔 Returns the VariableMap with all the values given to DoneCommand}}
  {{🦔 The conversation started has name `conversation_name`}}
  {{🦔 `start_message` is given as the initial message}}

  Returns:
    Output variables given to the final `done` command (extracted from the
    final message in the conversation).
  """
  raise NotImplementedError()  # {{🍄 run agent loop}}
