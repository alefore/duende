import asyncio
import logging
import os
import pathlib
import re
from typing import Any

import aiofiles

from agent_command import AgentCommand, Argument, ArgumentContentType, CommandOutput, CommandSyntax, VariableMap, VariableName
from file_access_policy import FileAccessPolicy
from code_specs import comment_string, ExpandedMarker, FileExtension, get_expanded_markers, get_markers, MarkerChar, MarkerName, MarkersOverlapError, MarkerImplementation, reindent_code
from validation import ValidationManager


def _get_file_extension(path: pathlib.Path) -> FileExtension:
  """Returns the file extension (sans the dot), handling `.dm.foo` files.

  {{🦔 Given 'foo.py', returns 'py'.}}
  {{🦔 Given 'src/foo.dm.py', returns 'py'.}}
  """
  raise NotImplementedError()  # {{🍄 get file extension}}


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
            Argument(
                name=VariableName("path"),
                arg_type=ArgumentContentType.PATH_INPUT_OUTPUT,
                description="The path of the file to update."),
            Argument(
                name=VariableName("marker_name"),
                arg_type=ArgumentContentType.STRING,
                description="The name of the marker to update."),
            Argument(
                name=VariableName("content"),
                arg_type=ArgumentContentType.STRING,
                description=(
                    "The new content for the marker implementation block. "
                    "This will replace all lines between the "
                    "\"✨ {marker_name}\" comment "
                    "and the following \"✨\" comment (in `path`)."))
        ],
        output_description="A string describing the result of the operation.")

  async def run(self, inputs: VariableMap) -> CommandOutput:
    """Updates the duende marker specified by the parameters in `inputs`.

    {{🦔 If `content` begins with a "✨ {marker_name}" comment, does not result
         in the file having that comment repeatedly.}}
    {{🦔 If `content` ends with a "✨" comment, does not result in the file
         having that line repeated (obviously, it may occur in other parts of
         the file).}}
    """
    path_str = str(inputs[VariableName("path")])
    marker_name_str = str(inputs[VariableName("marker_name")])
    content = str(inputs[VariableName("content")])

    path = pathlib.Path(path_str)

    if not self._file_access_policy.allow_access(path_str):
      raise NotImplementedError()  # {{🍄 return error CommandOutput policy}}

    try:
      async with aiofiles.open(path, mode='r') as f:
        lines = (await f.read()).splitlines()
    except Exception as e:
      raise NotImplementedError()  # {{🍄 return read error CommandOutput}}

    blocks = [
        m for m in get_expanded_markers(path) if m.name == marker_name_str
    ]

    # {{🍄 return error CommandOutput if blocks is empty}}
    # {{🍄 return error CommandOutput if blocks has more than one element}}

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

    new_file_content = "\n".join(new_lines)

    try:
      async with aiofiles.open(path, mode='w') as f:
        await f.write(new_file_content)
      if self._validation_manager:
        self._validation_manager.RegisterChange()
      raise NotImplementedError()  # {{🍄 return success CommandOutput}}
    except Exception as e:
      raise NotImplementedError()  # {{🍄 return error CommandOutput exception}}
