"""Supporting logic for DM-related workflows.md."""

# Suggested validator: MYPYPATH=~/coding-agent/src mypy $DMPATH

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

# Value is a comma-separated list of local files that someone implementing a DM
# marker may want to read.
relevant_paths_variable = VariableName('relevant_paths')


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


def reindent_code(code: str, desired_spaces: int) -> str:
  """Returns a copy of `code` with the desired leading spaces.

    First finds the longest whitespace prefix that all non-empty `code` lines
    contain and removes it (from all lines). Then prepends to all lines a prefix
    of the desired length.

    {{🦔 If an input line (from `code`) is empty or only contains whitespace
         characters, the corresponding line in the output is empty.}}
    {{🦔 If the whitespace prefixes are removed (from all input and output
         lines), the output is identical to `code`.}}
    {{🦔 All lines in the output must begin with `desired_spaces` spaces or
         be empty.}}
    {{🦔 The output must contain at least one line where, if `desired_spaces`
         spaces are removed (from the start), the line starts
         with a non-space character.}}
    """
  raise NotImplementedError()  # {{🍄 reindent code}}


class ExpandedMarker(NamedTuple):
  """Contains the position in a file of an expanded DM marker.

  The marker is a block of consecutive lines starting with a line containing
  only whitespace and the comment "✨ {name}" and ending in the first line
  (after the start) containing only whitespace and the comment "✨". The format
  of the command depends on the programming language of the file, determined by
  its file extension. (e.g., "  # ✨ foo  " is a valid start for a marker with
  name "foo" in a file that ends in `.py`). """

  name: str
  """Name of the marker (does not include the "✨" character)."""

  start_index: int
  """Index in the file of the line with the start comment ("# ✨ foo")."""

  end_index: int
  """Index in the file of the line with the end comment ("# ✨")."""

  contents: str
  """All the lines in the expanded marker (including start/end comment)."""


class RepeatedExpandedMarkersError(ValueError):
  """Two expanded markers with identical names were found."""


def get_expanded_markers(path: pathlib.Path) -> list[ExpandedMarker]:
  """Returns the expanded markers found in `path` in appearance order.

  {{🦔 Given an empty file, returns an empty list.}}
  {{🦔 Raises FileNotFoundError for a non-existent file}}
  {{🦔 Given an file with four different markers, returns a list with four
       elements. The outputs match the inputs: fields in the ExpandedMarker
       entries are correct, and the output order matches the input.}}
  {{🦔 Given a file with two different markers each ocurring twice, raises
       `RepeatedExpandedMarkersError`. The exception string mentions all
       repeated markers.}}
  """
  raise NotImplementedError()  # {{🍄 get expanded markers}}


class MarkersOverlapError(ValueError):
  """Two markers have a common line.

  This is invalid: markers may not overlap.
  """


def get_markers_str(char: MarkerChar,
                    input: str) -> dict[MarkerName, list[int]]:
  """Returns the positions (line index) of all markers in `path`.

  {{🦔 Returns {} for an empty input}}
  {{🦔 Returns {} for an input with 5 lines but no markers}}
  {{🦔 Correctly returns a marker in an input with just 1 marker}}
  {{🦔 If a marker starts in the first line in the input, its value in the
       output is [0].}}
  {{🦔 If a marker starts in the last line, its value in the output is
       `len(lines) - 1`.}}
  {{🦔 Correctly handles an input where a marker starts in the first line and
       finishes in the last line.}}
  {{🦔 Spaces are correctly removed from a marker named "  foo bar  ".}}
  {{🦔 Returns all markers in an input with ten markers.}}
  {{🦔 The index of markers returned in an input with ten markers is correct.}}
  {{🦔 An input can have repeated markers; the output just lists their
       positions.}}
  {{🦔 An input where two markers overlap (one ends in the same line where the
       other begins) raises `MarkersOverlapError`.}}
  {{🦔 The returned object is sorted by appearance order (i.e., iterating across
       the keys of the returned dictionary matches the order in which the first
       appearance of each marker was found in the input).}}

  Raises:
      MarkersOverlapError: if two markers share a common line.
  """
  raise NotImplementedError()  # {{🍄 get markers str}}


async def get_markers(char: MarkerChar,
                      path: pathlib.Path) -> dict[MarkerName, list[int]]:
  """Reads the file contents and calls `get_markers_str`.

  {{🦔 Reads `path` asynchronously}}
  {{🦔 Raises FileNotFoundError for a non-existent file}}
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
    {{🦔 Raises FileNotFoundError for a non-existent file.}}
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

  def __post_init__(self) -> None:
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

    {{🦔 Validation fails if the implementation contains markers (per
         `get_markers(MUSHROOM, …)`). In this case, a helpful string is
         returned, proposing an alternative along the lines of
         `"{{" + "🍄 …}}"` (which is enough to avoid this).}}
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

  def file_extension(self) -> FileExtension:
    """Returns the file extension of the `dm_path`.

    {{🦔 For `dm_path` "foo/bar/quux.dm.py", returns "py"}}
    """
    raise NotImplementedError()  # {{🍄 PathAndValidator file extension}}

  def output_path(self) -> pathlib.Path:
    """Returns `dm_path` without the `.dm` part.

    {{🦔 If `dm_path` is "foo/bar/quux.dm.py", returns "foo/bar/quux.py"}}
    """
    raise NotImplementedError()  # {{🍄 PathAndValidator output path}}

  def old_path(self) -> pathlib.Path:
    """Returns the "old" path, where the previous implementation is backed up.

    This is done by replacing the ".dm." part with ".old.".

    When expansion begins, we use these paths to make a copy of previous files
    that we'll overwrite.

    {{🦔 For `dm_path` "foo/bar.dm.py", returns "foo/bar.old.py".}}
    """
    raise NotImplementedError()  # {{🍄 PathAndValidator old path}}

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
