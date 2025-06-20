from typing import List, Optional
import os
import re  # Import the regex module

from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, ArgumentMultiline
from validation import ValidationManager
from file_access_policy import FileAccessPolicy
from selection_manager import Selection, SelectionManager


class SelectTextCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy,
               selection_manager: SelectionManager):
    self.file_access_policy = file_access_policy
    self.selection_manager = selection_manager

  def Name(self) -> str:
    return "select"

  def GetDescription(self) -> str:
    return (
        f"#{self.Name()} <path> <start line pattern> <end line pattern>: "
        "Creates a new selection for the content in the path specified starting at the first line matching "
        "<start line pattern> (a regex) and ending at the first following line matching <end line pattern> (a regex). "
        "The patterns are regular expressions, evaluated using Python's re module. "
        "The contents selected will be returned. "
        "Use select_overwrite to overwrite the selection with new contents. "
        "If your patterns contain spaces, you probably want to put quotes around them (e.g., #select my_foo.py 'def Foo' 'def Blah(')."
    )

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        description="Creates a new selection for the content in the path specified starting at the first line matching a start line regex pattern and ending at the first following line matching an end line regex pattern. The patterns are regular expressions, evaluated using Python's re module. The contents selected will be returned. Use select_overwrite to overwrite the selection with new contents. If your patterns contain spaces, you probably want to put quotes around them.",
        required=[
            Argument("path", ArgumentContentType.PATH_INPUT, "Path to the file."),
            Argument("start line pattern", ArgumentContentType.REGEX,
                     "The start line pattern."),
            Argument("end line pattern", ArgumentContentType.REGEX,
                     "The end line pattern.")
        ],)

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    self.selection_manager.clear_selection()

    if len(command_input.arguments) < 3:
      return CommandOutput(
          output=[],
          errors=[
              f"Arguments are missing, expected exactly 3: <path> <start line pattern> <end line pattern>."
          ],
          summary="Select command failed due to insufficient arguments.")

    if len(command_input.arguments) > 3:
      error_message = (
          f"Too many arguments were given. Expected exactly 3: <path> <start line pattern> <end line pattern>. Found:\n"
      )
      for i, arg in enumerate(command_input.arguments, start=1):
        if i <= 3:
          error_message += f"  arg {i} ({'path' if i == 1 else 'start line pattern' if i == 2 else 'end line pattern'}): \"{arg}\"\n"
        else:
          error_message += f"  arg {i} (unexpected!): \"{arg}\"\n"
      return CommandOutput(
          output=[],
          errors=[error_message],
          summary="Select command failed due to too many arguments.")

    path, start_line_pattern, end_line_pattern = command_input.arguments

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

  def GetDescription(self) -> str:
    return (
        f"#{self.Name()} <<\n… new contents …\n(multiple lines) …\n#end\n"
        "  Replaces the contents of the selection (the very last call to #select or similar command) with new contents."
    )

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        description="Replaces the contents of the selection (the very last call to #select or similar command) with new contents.",
        multiline=ArgumentMultiline(
            required=True,
            description="New contents to overwrite the current selection."))

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    if not command_input.multiline_content:
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
