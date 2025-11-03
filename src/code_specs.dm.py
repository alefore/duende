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
