# The default validator for expanding this file should be:
#
#     MYPYPATH=~/coding-agent/src mypy $DMPATH

import asyncio
import difflib
import logging
import os
import pathlib
import re
from typing import Any

import aiofiles

from agent_command import AgentCommand, Argument, ArgumentContentType, CommandOutput, CommandSyntax, REASON_VARIABLE, VariableMap, VariableName, VariableValue, VariableValueStr
from file_access_policy import FileAccessPolicy
from code_specs import comment_string, ExpandedMarker, FileExtension, get_expanded_markers, get_markers, MarkerChar, MarkerName, MarkersOverlapError, MarkerImplementation, reindent_code, RepeatedExpandedMarkersError
from validation import ValidationManager

_PATH_VARIABLE = VariableName("path")
_MARKER_NAME_VARIABLE = VariableName("marker_name")
_CONTENT_VARIABLE = VariableName("content")


def _get_file_extension(path: pathlib.Path) -> FileExtension:
  """Returns the file extension (sans the dot), handling `.dm.foo` files.

  {{🦔 Given 'foo.py', returns 'py'.}}
  {{🦔 Given 'src/foo.dm.py', returns 'py'.}}
  """
  raise NotImplementedError()  # {{🍄 get file extension}}


class MarkerUpdateError(ValueError):
  pass


class ListDuendeMarkerImplementationCommand(AgentCommand):

  def __init__(self,
               file_access_policy: FileAccessPolicy,
               validation_manager: ValidationManager | None = None):
    self._file_access_policy = file_access_policy
    self._validation_manager = validation_manager

  def Name(self) -> str:
    return "list_duende_implementation_markers"

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name=VariableName("list_duende_implementation_marker"),
        description="Lists all Duende implementation markers in a file.",
        arguments=[
            REASON_VARIABLE,
            Argument(
                name=_PATH_VARIABLE,
                arg_type=ArgumentContentType.PATH_INPUT_OUTPUT,
                description="The path of the file to list markers from."),
        ])

  async def run(self, inputs: VariableMap) -> CommandOutput:
    path = inputs[_PATH_VARIABLE]
    assert isinstance(path, pathlib.Path)
    try:
      blocks = get_expanded_markers(path)
    except FileNotFoundError as e:
      raise  # {{🍄 list: return error output exception file not found}}
    except RepeatedExpandedMarkersError as e:
      raise  # {{🍄 list: return error output exception repeated markers}}
    raise NotImplementedError()  # {{🍄 return output listing all blocks}}


class ReadDuendeImplementationMarkerCommand(AgentCommand):

  def __init__(self,
               file_access_policy: FileAccessPolicy,
               validation_manager: ValidationManager | None = None):
    self._file_access_policy = file_access_policy
    self._validation_manager = validation_manager

  def Name(self) -> str:
    return "read_duende_implementation_marker"

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name=VariableName("read_duende_implementation_marker"),
        description="Reads a Duende implementation marker from a file.",
        arguments=[
            REASON_VARIABLE,
            Argument(
                name=_PATH_VARIABLE,
                arg_type=ArgumentContentType.PATH_INPUT_OUTPUT,
                description="The path of the file to read from."),
            Argument(
                name=_MARKER_NAME_VARIABLE,
                arg_type=ArgumentContentType.STRING,
                description="The name of the marker to read."),
        ],
        output_description="The entire contents of the marker.")

  async def run(self, inputs: VariableMap) -> CommandOutput:
    """Returns the contents of a given marker.

    {{🦔 If the marker is not found in the file, returns an error. The error
         includes the explicit list of all markers found in the file (or an
         explicit explanation if the file contains no markers.}}
    """
    path = inputs[_PATH_VARIABLE]
    assert isinstance(path, pathlib.Path)
    marker_name = inputs[_MARKER_NAME_VARIABLE]
    assert isinstance(marker_name, str)
    try:
      blocks = get_expanded_markers(path)
    except FileNotFoundError as e:
      raise  # {{🍄 read: return error output exception file not found}}
    except RepeatedExpandedMarkersError as e:
      raise  # {{🍄 read: return error output exception repeated markers}}
    block = [b for b in blocks if b.name == marker_name]
    if not block:
      raise NotImplementedError()  # {{🍄 read: raise if block is empty}}
    assert len(block) == 1
    raise NotImplementedError()  # {{🍄 read: return contents from block[0]}}


class UpdateDuendeMarkerImplementationCommand(AgentCommand):

  def __init__(self,
               file_access_policy: FileAccessPolicy,
               validation_manager: ValidationManager | None = None):
    self._file_access_policy = file_access_policy
    self._validation_manager = validation_manager

  def Name(self) -> str:
    return "update_duende_marker_implementation"

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name=VariableName("update_duende_marker_implementation"),
        description="Updates a Duende marker implementation block in a file.",
        arguments=[
            REASON_VARIABLE,
            Argument(
                name=_PATH_VARIABLE,
                arg_type=ArgumentContentType.PATH_INPUT_OUTPUT,
                description="The path of the file to update."),
            Argument(
                name=_MARKER_NAME_VARIABLE,
                arg_type=ArgumentContentType.STRING,
                description="The name of the marker to update."),
            Argument(
                name=_CONTENT_VARIABLE,
                arg_type=ArgumentContentType.STRING,
                description=(
                    "The new content for the marker implementation block. "
                    "This will replace all lines between the "
                    "\"✨ {marker_name}\" comment "
                    "and the following \"✨\" comment (in `path`)."))
        ],
        output_description="A string describing the result of the operation.")

  async def _get_updated_content(self, path: pathlib.Path, marker_name: str,
                                 content: str) -> str:
    """Loads contents from `path` and returns them replacing `marker_name`.

    {{🦔 Only reads `path`, does not modify it.}}
    {{🦔 Raises MarkerUpdateError on any invalid condition: marker is not found,
         file can't be read, marker is duplicated in the file.}}
    {{🦔 If the marker is not found, the `MarkerUpdateError` exception includes
         a list of all available markers.}}
    {{🦔 `content` may start with the marker-start comment but it doesn't
         need to. Correctly handles both cases (without repeating the
         marker-start comment in the output). Same for the marker-end comment.}}
    """
    try:
      async with aiofiles.open(path, mode='r') as f:
        lines = (await f.read()).splitlines()
    except Exception as e:
      raise NotImplementedError()  # {{🍄 raise MarkerUpdateError: read}}

    all_blocks = get_expanded_markers(path)
    blocks = [m for m in all_blocks if m.name == marker_name]

    # {{🍄 raise MarkerUpdateError if blocks is empty}}
    # {{🍄 raise MarkerUpdateError if len(blocks) > 1}}

    block: ExpandedMarker = blocks[0]

    marker_line = lines[block.start_index]
    marker_indentation = len(marker_line) - len(marker_line.lstrip())

    content_lines: list[str] = content.splitlines()

    # Conditionally remove start/end comments if they are in `content`:
    # {{🍄 conditionally remove marker start from content}}
    # {{🍄 conditionally remove marker end from content}}

    indented_content = reindent_code("\n".join(content_lines),
                                     marker_indentation)

    new_lines = []
    new_lines.extend(lines[:block.start_index + 1])
    new_lines.append(indented_content)
    new_lines.extend(lines[block.end_index:])

    return "".join(f"{l}\n" for l in new_lines)

  async def _get_full_diff(self, path: pathlib.Path,
                           new_content: str) -> list[str] | None:
    if not await asyncio.to_thread(os.path.exists, path):
      return None

    async with aiofiles.open(path, "r") as f:
      original_content_lines: list[str] = (await f.read()).splitlines()
    return list(
        difflib.unified_diff(
            original_content_lines,
            new_content.splitlines(),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            lineterm="",
        ))

  async def derive_args(self, inputs: VariableMap) -> VariableMap:
    output = VariableMap({})
    path = pathlib.Path(str(inputs[_PATH_VARIABLE]))
    marker_name = inputs[_MARKER_NAME_VARIABLE]
    assert isinstance(marker_name, str)
    content = inputs[_CONTENT_VARIABLE]
    assert isinstance(content, str)

    try:
      async with aiofiles.open(path, mode='r') as f:
        lines = (await f.read()).splitlines()
      updated_content = await self._get_updated_content(path, marker_name,
                                                        content)
      output[VariableName("content_diff")] = await self._derive_diff(
          path, VariableValueStr(updated_content))
    except Exception as e:
      pass
    return output

  async def _derive_diff(self, path: pathlib.Path,
                         new_content: VariableValueStr) -> VariableValue:
    try:
      diff = await self._get_full_diff(path, new_content)
      if diff is None:
        return VariableValueStr("File is new.")
      elif not diff:
        return VariableValueStr("No changes.")
      else:
        return VariableValueStr("\n".join(diff))
    except Exception as e:
      return VariableValueStr(f"Could not compute diff: {e}")

  async def run(self, inputs: VariableMap) -> CommandOutput:
    path_str = str(inputs[_PATH_VARIABLE])
    marker_name = str(inputs[_MARKER_NAME_VARIABLE])
    content = str(_CONTENT_VARIABLE)

    path = pathlib.Path(path_str)

    if not self._file_access_policy.allow_access(path_str):
      raise NotImplementedError()  # {{🍄 return error CommandOutput policy}}

    try:
      updated_content = await self._get_updated_content(path, marker_name,
                                                        content)
      async with aiofiles.open(path, mode='w') as f:
        await f.write(updated_content)
      if self._validation_manager:
        self._validation_manager.RegisterChange()
      raise NotImplementedError()  # {{🍄 return success CommandOutput}}
    except Exception as e:
      raise NotImplementedError()  # {{🍄 return error CommandOutput exception}}
