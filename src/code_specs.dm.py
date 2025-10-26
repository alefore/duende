"""Supporting logic for DM-related workflows.md."""

import aiofiles
import asyncio
import collections
import dataclasses
import itertools
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

  `input` may contain multiple lines.

  Supported extensions: py, sh, cc, h, js, ts, java, html, css

  {{🦔 "py" and "foo bar" returns "# foo bar"}}
  {{🦔 "html" and "my test" returns "<!-- my test -->"}}
  {{🦔 "html" and "foo\nbar\nquux" returns "<!-- foo\nbar\nquux -->"}}
  {{🦔 "cc" and "foo\nbar" returns "// foo\n//bar"}}
  {{🦔 "css" and "foo bar" returns "/* foo bar */"}}
  {{🦔 "css" and "foo\nbar" returns "/* foo\nbar */"}}
  """
  #  {{🍄 get comment char}}
  raise ValueError(f"Unknown file extension: {file_extension}")


@dataclasses.dataclass(frozen=True)
class MarkerName:
  char: MarkerChar
  name: str

  def __post_init__(self) -> None:
    object.__setattr__(self, 'name', self._fix_name(self.name))

  def _fix_name(self, name: str) -> str:
    """Fixes `name`, replacing any sequence of whitespace characters by ' '.

    Whitespace characters at the beginning and end are removed.

    {{🦔 Name " foo" is turned into "foo".}}
    {{🦔 Name "foo " is turned into "foo".}}
    {{🦔 Name " foo " is turned into "foo".}}
    {{🦔 Name "Foo\nBar" is turned into "Foo Bar".}}
    {{🦔 Name "  foo \n\n   \n   bar  " is turned into "foo bar".}}
    """
    raise NotImplementedError()  # {{🍄 MarkerName fix name}}


class MarkersOverlapError(ValueError):
  """Two markers have a common line.

  This is invalid: markers may not overlap.
  """


async def get_markers(char: MarkerChar,
                      path: pathlib.Path) -> dict[MarkerName, list[int]]:
  """Returns the positions (line index) of all markers in `path`.

  {{🦔 Reads `path` asynchronously}}
  {{🦔 Returns {} for an empty file}}
  {{🦔 Raises FileNotFound for a non-existent file}}
  {{🦔 Returns {} for a file with 5 lines but no markers}}
  {{🦔 Correctly returns a marker in a file with just 1 marker}}
  {{🦔 If a marker starts in the first line in the file, its value in the output
       is [0].}}
  {{🦔 If a marker starts in the last line, its value in the output is
       `len(lines) - 1`.}}
  {{🦔 Correctly handles a file where a marker starts in the first line and
       finishes in the last line.}}
  {{🦔 Spaces are correctly removed from a marker named "  foo bar  ".}}
  {{🦔 Returns all markers in a file with ten markers.}}
  {{🦔 The index of markers returned in a file with ten markers is correct.}}
  {{🦔 A file can have repeated markers; the output just lists their
       positions.}}
  {{🦔 A file where two markers overlap (one ends in the same line where the
       other begins) raises `MarkersOverlapError`.}}
  {{🦔 The returned object is sorted by appearance order (i.e., iterating across
       the keys of the returned dictionary matches the order in which the first
       appearance of each marker was found in the file).}}

  Raises:
      MarkersOverlapError: if two markers share a common line.
  """
  raise NotImplementedError()  # {{🍄 get markers}}


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

    {{🦔 The read operation is async.}}
    {{🦔 The write operation is async.}}
    {{🦔 Successfully expands a marker in a file with a single marker.}}
    {{🦔 Successfully expands a marker that spans multiple lines (i.e., that
         has newline characters in the name).}}
    {{🦔 Successfully expands the correct marker in a file with ten markers.}}
    {{🦔 The value is stored literally, without adding any leading spaces.}}
    {{🦔 Raises ValueError if the marker doesn't occur in `path`}}
    {{🦔 Raises ValueError if the marker occurs twice in `path`}}
    {{🦔 Raises FileNotFound if the file does not exist}}
    {{🦔 Raises ValueError if `path` contains a ".dm." part}}
    {{🦔 The value written (the implementation) is reindented according to the
         rules of `_value_indent`; the number of desired spaces is equal to the
         number of spaces before the first non-space character in the line that
         contains the marker.}}
    {{🦔 Uses `get_markers` rather than redundantly implementing its logic.}}

    Raises:
      ValueError if `path` has a `.dm.` part. DM files themselves should never
      be updated.
    """
    raise NotImplementedError()  # {{🍄 marker implementation save}}

  def _value_indent(self, desired_spaces: int) -> str:
    """Returns a copy of `_value` with the desired leading spaces.

    First finds the longest whitespace prefix that all non-empty `_value` lines
    contain and removes it (from all lines). Then prepends to all lines a prefix
    of the desired length.

    {{🦔 If an input line (from `_value`) is empty or only contains whitespace
         characters, the corresponding line in the output is empty.}}
    {{🦔 If the whitespace prefixes are removed (from all input and output
         lines), the output is identical to `_value`.}}
    {{🦔 All lines in the output must begin with `desired_spaces` spaces or
         be empty.}}
    {{🦔 The output must contain at least one line where, if `desired_spaces`
         spaces are removed (from the start), the line starts
         with a non-space character.}}
    """
    raise NotImplementedError()  # {{🍄 marker implementation value indent}}


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
    {{🦔 Uses `implementation.save` on the temporary copy of `source` (in order
         to update the implementation of the marker in the file).}}
    """
    raise NotImplementedError()  # {{🍄 implement validator}}


@dataclasses.dataclass(frozen=True)
class PathAndValidator:
  """An immutable container for a DM file path and a validator."""
  dm_path: pathlib.Path
  validator: Validator

  async def validate_fields(self) -> None:
    """Validates fields, conditionally raising ValueError.

    When searching for markers, uses MarkerChar('🍄').

    {{🦔 Doesn't raise if `dm_path` is a valid file with two 🍄 markers.}}
    {{🦔 Raises ValueError if `dm_path` is "foo.py" (lacks the `.dm.` part).}}
    {{🦔 Raises ValueError if `dm_path` is a valid file with no 🍄 markers.}}
    {{🦔 Raises ValueError if `dm_path` contains a repeated 🍄 marker.}}

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


async def prepare_initial_message(start_message_content: str,
                                  relevant_files: set[pathlib.Path]) -> Message:
  """Creates the first message for an AgentLoop conversation.

  {{🦔 `relevant_files` are read asynchronously.}}
  {{🦔 The output contains `start_message_content` as its first section.}}
  {{🦔 If `relevant_files` is empty, the output has just one section.}}
  {{🦔 If a relevant file can't be read, raises an exception (or, rather, lets
       the underlying exception bubble up, doesn't catch it).}}
  {{🦔 There is a content section in the start message given to the AgentLoop
       for each entry in `relevant_files`. It starts with a line "File '{path}'
       follows:" (with the corresponding path) and includes the entire contents
       of the file.}}
  """
  raise NotImplementedError()  # {{🍄 prepare initial message}}


async def prepare_command_registry(
    done_command_arguments: list[Argument],
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

  {{🦔 Returns the `VariableMap` with all the values given to `DoneCommand`.}}
  {{🦔 The conversation started has name `conversation_name`.}}
  {{🦔 `start_message` is given as the initial message.}}

  Returns:
    Output variables given to the final `done` command (extracted from the
    final message in the conversation).
  """
  raise NotImplementedError()  # {{🍄 run agent loop}}
