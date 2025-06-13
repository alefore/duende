from typing import List, Optional
import os

from agent_command import AgentCommand, CommandInput, CommandOutput
from file_access_policy import FileAccessPolicy


class Selection:

  def __init__(self, path: str, start_line_content: str,
               end_line_content: str) -> None:
    self.path = path
    self.start_line_content = start_line_content
    self.end_line_content = end_line_content
    self.selected_lines: List[str] = []

  def Read(self) -> List[str]:
    """Reads corresponding lines from the file and returns them."""
    if not os.path.exists(self.path):
      raise FileNotFoundError(f"File not found: {self.path}")

    with open(self.path, "r") as file:
      lines: List[str] = file.readlines()

    # TODO: Change start_index and end_index to Optional[int]. I think None is
    # a cleaner value than -1. Add the type explicitly and adjust customers.
    start_index = end_index = -1
    for index, line in enumerate(lines):
      if start_index == -1 and self.start_line_content in line:
        start_index = index
      elif start_index != -1 and self.end_line_content in line:
        end_index = index
        break

    if start_index == -1:
      raise ValueError("Could not find the specified start line content.")
    if end_index == -1:
      raise ValueError("Could not find the specified end line content.")

    self.selected_lines = lines[start_index:end_index + 1]
    return self.selected_lines

  def Overwrite(self, new_contents: List[str]):
    """
    Replaces the selection with new contents (deleting previous contents).
    'new_contents' should not include newline characters at the end of each line.
    The file (self.path) will be updated on disk.
    """
    if not os.path.exists(self.path):
      raise FileNotFoundError(f"File not found: {self.path}")

    with open(self.path, "r") as file:
      lines = file.readlines()

    start_index = None
    for index, line in enumerate(lines):
      if self.start_line_content in line:
        start_index = index
        break

    if start_index is None:
      raise ValueError("Could not find the specified start line content.")

    end_index = None
    for index in range(start_index, len(lines)):
      if self.end_line_content in lines[index]:
        end_index = index
        break

    if end_index is None:
      raise ValueError("Could not find the specified end line content.")

    # Replace lines between start_index and end_index
    # Add newline characters back to each line in 'new_contents'
    new_contents_with_newlines = [f"{line}\n" for line in new_contents]
    lines = lines[:start_index] + new_contents_with_newlines + lines[end_index +
                                                                     1:]

    with open(self.path, "w") as file:
      file.writelines(lines)


current_selection: Optional[Selection] = None


class SelectTextCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

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
    global current_selection

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
      current_selection = Selection(path, start_line_content, end_line_content)
      selected_lines = current_selection.Read()
      return CommandOutput(
          output=[f"select <<\n{''.join(selected_lines)}\n#end ({path})"],
          errors=[],
          summary=f"Selected content from file {path}.")
    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"select: {str(e)}"],
          summary=f"Select command error: {str(e)}")


class SelectOverwriteCommand(AgentCommand):

  def GetDescription(self) -> str:
    return "select_overwrite <<\\n … new contents …\\n #end: Replaces the contents of the selection with new contents."

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    global current_selection

    if not command_input.multiline_content:
      return CommandOutput(
          output=[],
          errors=["select_overwrite requires new contents as multiline input."],
          summary="Select overwrite failed due to missing content.")

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
