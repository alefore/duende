import asyncio
import os
import pathlib
import re
from typing import Any

from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, VariableName
from validation import ValidationManager
from file_access_policy import FileAccessPolicy
from selection_manager import Selection, SelectionManager, StartPatternNotFound, EndPatternNotFound


class SelectCommand(AgentCommand):

  def __init__(self,
               file_access_policy: FileAccessPolicy,
               selection_manager: SelectionManager,
               use_regex: bool = False):
    self.file_access_policy = file_access_policy
    self.selection_manager = selection_manager
    self.use_regex = use_regex

  def Name(self) -> str:
    return self.Syntax().name

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="select_regex" if self.use_regex else "select",
        description="Creates a new selection for the content in the path specified. The selection starts at the first line matching a start pattern and ends at the first following line matching an optional end pattern. If no end pattern is provided, only the line matching the start pattern is selected. The contents selected will be returned. Use select_overwrite to overwrite the selection with new contents. If your patterns contain spaces, you probably want to put quotes around them.",
        arguments=[
            Argument(
                name=VariableName("path"),
                arg_type=ArgumentContentType.PATH_INPUT,
                description="Path to the file to select from.",
                required=True),
            Argument(
                name=VariableName("start_line_pattern"),
                arg_type=ArgumentContentType.STRING,
                description="The start line pattern.",
                required=True),
            Argument(
                name=VariableName("end_line_pattern"),
                arg_type=ArgumentContentType.STRING,
                description="The end line pattern. If omitted, only the start line is selected.",
                required=False)
        ])

  async def run(self, inputs: dict[VariableName, Any]) -> CommandOutput:
    self.selection_manager.clear_selection()

    path = inputs[VariableName('path')]
    assert isinstance(path, pathlib.Path)
    start_line_pattern_raw = inputs[VariableName('start_line_pattern')]
    end_line_pattern_raw: str | None = inputs.get(
        VariableName('end_line_pattern'))

    if self.use_regex:
      start_line_pattern = start_line_pattern_raw
      end_line_pattern = end_line_pattern_raw
    else:
      start_line_pattern = re.escape(start_line_pattern_raw)
      end_line_pattern = re.escape(
          end_line_pattern_raw) if end_line_pattern_raw is not None else None

    try:
      selection = await Selection.FromLinePattern(
          str(path), start_line_pattern, end_line_pattern)
      selected_lines = await selection.Read()
      self.selection_manager.set_selection(selection)
      return CommandOutput(
          output="select <<\n" + "\n".join(selected_lines) + f"\n#end ({path})",
          errors="",
          summary=selection.ProvideSummary(),
          command_name=self.Name())
    except StartPatternNotFound:
      return CommandOutput(
          output="",
          errors=f"{self.Name()}: Could not find start pattern '{start_line_pattern_raw}' in {path}.",
          summary="Select command error: start pattern not found.",
          command_name=self.Name())
    except EndPatternNotFound:
      return CommandOutput(
          output="",
          errors=f"{self.Name()}: Could not find end pattern '{end_line_pattern_raw}' in {path} after finding start pattern.",
          summary="Select command error: end pattern not found.",
          command_name=self.Name())
    except Exception as e:
      return CommandOutput(
          output="",
          errors=f"{self.Name()}: {str(e)}",
          summary=f"Select command error: {str(e)}",
          command_name=self.Name())


class SelectOverwriteCommand(AgentCommand):

  def __init__(self, selection_manager: SelectionManager,
               validation_manager: ValidationManager | None):
    self.selection_manager = selection_manager
    self.validation_manager = validation_manager

  def Name(self) -> str:
    return self.Syntax().name

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        name="select_overwrite",
        description="Replaces the contents of the selection (the very last call to #select or similar command) with new contents.",
        arguments=[
            Argument(
                name=VariableName("content"),
                arg_type=ArgumentContentType.STRING,
                description="New contents to overwrite the current selection.",
                required=True),
            Argument(
                name=VariableName("reason"),
                arg_type=ArgumentContentType.STRING,
                description="Brief (one or two sentences) explanation of why you are issuing this command (what you want to accomplish).",
                required=False)
        ])

  async def run(self, inputs: dict[VariableName, Any]) -> CommandOutput:
    content = inputs[VariableName("content")]

    current_selection = self.selection_manager.get_selection()

    if current_selection is None:
      return CommandOutput(
          output="",
          errors="No selection exists (call #select first?).",
          summary="Select overwrite failed because no selection exists.",
          command_name=self.Name())

    try:
      await current_selection.Overwrite(content)
      if self.validation_manager:
        self.validation_manager.RegisterChange()
      line_count = len(content.splitlines())
      return CommandOutput(
          output="The selection was successfully overwritten.",
          errors="",
          summary=f"Successfully overwrote the selection with {line_count} lines.",
          command_name=self.Name())
    except Exception as e:
      return CommandOutput(
          output="",
          errors=f"Error overwriting selection: {str(e)}",
          summary="Select overwrite encountered an error.",
          command_name=self.Name())
