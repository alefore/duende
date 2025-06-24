from typing import List, Optional
import os
import re  # Import the regex module

from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, ArgumentMultiline
from validation import ValidationManager
from file_access_policy import FileAccessPolicy
from selection_manager import Selection, SelectionManager


class SelectCommand(AgentCommand):

  def __init__(self,
               file_access_policy: FileAccessPolicy,
               selection_manager: SelectionManager,
               use_regex: bool = False):
    self.file_access_policy = file_access_policy
    self.selection_manager = selection_manager
    self.use_regex = use_regex

  def Name(self) -> str:
    return "select_regex" if self.use_regex else "select"

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        description="Creates a new selection for the content in the path specified. The selection starts at the first line matching a start pattern and ends at the first following line matching an optional end pattern. If no end pattern is provided, only the line matching the start pattern is selected. The contents selected will be returned. Use select_overwrite to overwrite the selection with new contents. If your patterns contain spaces, you probably want to put quotes around them.",
        required=[
            Argument("path", ArgumentContentType.PATH_INPUT,
                     "Path to the file."),
            Argument("start_line_pattern", ArgumentContentType.STRING,
                     "The start line pattern.")
        ],
        optional=[
            Argument(
                "end_line_pattern", ArgumentContentType.STRING,
                "The end line pattern. Optional. If omitted, only the start line is selected."
            )
        ])

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    self.selection_manager.clear_selection()

    args = command_input.arguments
    args_len = len(args)

    if args_len < 2 or args_len > 3:
      return CommandOutput(
          output=[],
          errors=[
              f"Incorrect number of arguments. Expected: <path> <start_pattern> [end_pattern]. Received {args_len}."
          ],
          summary="Select command failed due to incorrect argument count.")

    path = args[0]
    start_line_pattern_raw = args[1]
    end_line_pattern_raw = args[2] if args_len == 3 else start_line_pattern_raw

    if self.use_regex:
      start_line_pattern = start_line_pattern_raw
      end_line_pattern = end_line_pattern_raw
    else:
      start_line_pattern = re.escape(start_line_pattern_raw)
      end_line_pattern = re.escape(end_line_pattern_raw)

    if not self.file_access_policy.allow_access(path):
      return CommandOutput(
          output=[],
          errors=[f"The file '{path}' was not found."],
          summary="Select command failed because the file was not found.")

    try:
      selection = Selection.FromLinePattern(path, start_line_pattern,
                                            end_line_pattern)
      selected_lines = selection.Read()
      self.selection_manager.set_selection(selection)
      return CommandOutput(
          output=["select <<"] + selected_lines + [f"#end ({path})"],
          errors=[],
          summary=selection.ProvideSummary())
    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"{self.Name()}: {str(e)}"],
          summary=f"Select command error: {str(e)}")


class SelectOverwriteCommand(AgentCommand):

  def __init__(self, selection_manager: SelectionManager,
               validation_manager: Optional[ValidationManager]):
    self.selection_manager = selection_manager
    self.validation_manager = validation_manager

  def Name(self) -> str:
    return "select_overwrite"

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        description="Replaces the contents of the selection (the very last call to #select or similar command) with new contents.",
        multiline=ArgumentMultiline(
            required=True,
            description="New contents to overwrite the current selection."))

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    if command_input.multiline_content is None:
      return CommandOutput(
          output=[],
          errors=["select_overwrite requires new contents as multiline input."],
          summary="Select overwrite failed due to missing content.")

    current_selection = self.selection_manager.get_selection()

    if current_selection is None:
      return CommandOutput(
          output=[],
          errors=["No selection exists (call #select first?)."],
          summary="Select overwrite failed because no selection exists.")

    try:
      current_selection.Overwrite(command_input.multiline_content)
      if self.validation_manager:
        self.validation_manager.RegisterChange()
      line_count = len(command_input.multiline_content)
      return CommandOutput(
          output=["The selection was successfully overwritten."],
          errors=[],
          summary=f"Successfully overwrote the selection with {line_count} lines."
      )
    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"Error overwriting selection: {str(e)}"],
          summary="Select overwrite encountered an error.")
