from typing import List
import os

from agent_command import AgentCommand, CommandInput, CommandOutput
from file_access_policy import FileAccessPolicy
from selection_manager import Selection, SelectionManager


class SelectTextCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy,
               selection_manager: SelectionManager):
    self.file_access_policy = file_access_policy
    self.selection_manager = selection_manager

  def GetDescription(self) -> str:
    return (
        "#select <path> <start line content> <end line content>: "
        "Creates a new selection for the content in the path specified starting at the first line containing "
        "<start line content> and ending at the first following line containing <end line content>. "
        "The contents selected will be returned. "
        "Use select_overwrite to overwrite the selection with new contents. "
        "If your patterns contain spaces, you probably want to put quotes around them (e.g., #select my_foo.py 'def Foo' 'def Blah(')."
    )

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    if len(command_input.arguments) != 3:
      return CommandOutput(
          output=[],
          errors=[
              "select requires exactly three arguments: <path> <start_line_content> <end_line_content>."
          ],
          summary="Select command failed due to incorrect arguments.")

    path, start_line_content, end_line_content = command_input.arguments

    if not self.file_access_policy.allow_access(path):
      return CommandOutput(
          output=[],
          errors=[f"Access to '{path}' is not allowed."],
          summary="Select command access denied.")

    try:
      selection = Selection.FromLineContent(path, start_line_content,
                                            end_line_content)
      selected_lines = selection.Read()
      self.selection_manager.set_selection(selection)
      return CommandOutput(
          output=[f"select <<\n{''.join(selected_lines)}\n#end ({path})"],
          errors=[],
          summary=f"Selected from {path}: lines: {len(selected_lines)}")
    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"select: {str(e)}"],
          summary=f"Select command error: {str(e)}")


class SelectOverwriteCommand(AgentCommand):

  def __init__(self, selection_manager: SelectionManager):
    self.selection_manager = selection_manager

  def GetDescription(self) -> str:
    return "select_overwrite <<\\n … new contents …\\n #end: Replaces the contents of the selection with new contents."

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
      return CommandOutput(
          output=["The selection was successfully overwritten."],
          errors=[],
          summary="Successfully overwrote the selection.")
    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"Error overwriting selection: {str(e)}"],
          summary="Select overwrite encountered an error.")
