import asyncio
import logging
import os
import pathlib
import re
from typing import Any

import aiofiles

from agent_command import AgentCommand, Argument, ArgumentContentType, CommandOutput, CommandSyntax, VariableMap, VariableName
from file_access_policy import FileAccessPolicy
from code_specs import comment_string, FileExtension, get_markers, MarkerChar, MarkerName, MarkersOverlapError, MarkerImplementation
from validation import ValidationManager


class UpdateDuendeMarkerImplementation(AgentCommand):

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
                description="The new content for the marker implementation block."
            )
        ],
        output_description="A string describing the result of the operation.")

  async def run(self, inputs: VariableMap) -> CommandOutput:
    path_str = str(inputs[VariableName("path")])
    marker_name_str = str(inputs[VariableName("marker_name")])
    content = str(inputs[VariableName("content")])

    path = pathlib.Path(path_str)

    # 1. Check file access policy
    if not self._file_access_policy.allow_access(path_str):
      return CommandOutput(
          command_name=self.Name(),
          output="",
          errors=f"File access denied for writing to {path_str}.",
          summary=f"Failed to update marker in {path_str}: access denied.")

    # 2. Check if file exists
    if not await asyncio.to_thread(os.path.exists, path):
      return CommandOutput(
          command_name=self.Name(),
          output="",
          errors=f"File not found: {path_str}.",
          summary=f"Failed to update marker in {path_str}: file not found.")

    # Determine file extension for commenting
    file_extension_str = path.suffix.lstrip('.')
    if '.dm.' in path.name:
      parts = path.name.split('.')
      try:
        dm_index = parts.index('dm')
        if dm_index + 1 < len(parts):
          file_extension_str = parts[dm_index + 1]
        else:
          file_extension_str = ''
      except ValueError:
        file_extension_str = path.suffix.lstrip('.')
    file_extension = FileExtension(file_extension_str)

    # 3. Read the file content
    async with aiofiles.open(
        path, mode='r') as f:
      lines = (await f.read()).splitlines()

    # 4. Find the start and end of the marker block
    start_marker_text = comment_string(file_extension,
                                       f"✨ {marker_name_str}").strip()
    end_marker_text = comment_string(file_extension, "✨").strip()

    marker_start_line_idx = -1
    marker_end_line_idx = -1
    found_markers_count = 0

    for i, line in enumerate(lines):
      if line.strip() == start_marker_text:
        if marker_start_line_idx != -1:
          found_markers_count += 1  # Found a duplicate start marker
        marker_start_line_idx = i
      elif line.strip(
      ) == end_marker_text and marker_start_line_idx != -1 and marker_end_line_idx == -1:
        marker_end_line_idx = i

    if marker_start_line_idx == -1:
      return CommandOutput(
          command_name=self.Name(),
          output="",
          errors=f"Start marker '{start_marker_text}' not found in '{path_str}'.",
          summary=f"Failed to update marker in {path_str}: start marker not found."
      )

    if found_markers_count > 0:
      return CommandOutput(
          command_name=self.Name(),
          output="",
          errors=f"Multiple start markers named '{marker_name_str}' found in '{path_str}'. Marker names must be unique for updates.",
          summary=f"Failed to update marker in {path_str}: duplicate start marker names."
      )

    if marker_end_line_idx == -1 or marker_end_line_idx <= marker_start_line_idx:
      return CommandOutput(
          command_name=self.Name(),
          output="",
          errors=f"End marker '{end_marker_text}' not found after start marker or is incorrectly placed for '{marker_name_str}' in '{path_str}'.",
          summary=f"Failed to update marker in {path_str}: end marker not found or misplaced."
      )

    # 5. Determine the indentation of the start marker line
    marker_line = lines[marker_start_line_idx]
    indentation = len(marker_line) - len(marker_line.lstrip())
    indent_str = " " * indentation

    # 6. Prepare new content, skipping redundant marker lines if present in the input content
    processed_content_lines = content.splitlines()

    # Remove start/end markers if they are part of the input content
    if processed_content_lines and processed_content_lines[0].strip(
    ) == start_marker_text:
      processed_content_lines = processed_content_lines[1:]

    if processed_content_lines and processed_content_lines[-1].strip(
    ) == end_marker_text:
      processed_content_lines = processed_content_lines[:-1]

    # Simplify indentation logic using generator expression
    non_empty_lines = [line for line in processed_content_lines if line.strip()]
    if not non_empty_lines:
      min_common_indent = 0
    else:
      min_common_indent = min(
          len(line) - len(line.lstrip()) for line in non_empty_lines)

    normalized_and_indented_lines = []
    for line in processed_content_lines:
      if not line.strip():
        normalized_and_indented_lines.append("")
      else:
        normalized_and_indented_lines.append(indent_str +
                                             line[min_common_indent:])

    indented_content = "\n".join(normalized_and_indented_lines)

    # 7. Reconstruct the file content
    new_lines = []
    new_lines.extend(lines[:marker_start_line_idx +
                           1])  # Lines before and including the start marker
    new_lines.append(indented_content)  # Insert the new content
    new_lines.extend(
        lines[marker_end_line_idx:])  # Lines from the end marker onwards

    new_file_content = "\n".join(new_lines)

    # 8. Write the updated content back to the file
    try:
      async with aiofiles.open(path, mode='w') as f:
        await f.write(new_file_content)
      if self._validation_manager:
        self._validation_manager.RegisterChange()

      return CommandOutput(
          command_name=self.Name(),
          output=f"Successfully updated marker '{marker_name_str}' in '{path_str}'.",
          errors="",
          summary=f"Updated marker '{marker_name_str}' in '{path_str}'.")
    except Exception as e:
      return CommandOutput(
          command_name=self.Name(),
          output="",
          errors=f"Error writing to {path_str}: {str(e)}",
          summary=f"{self.Name()} command encountered an error.")
