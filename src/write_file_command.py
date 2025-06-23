from typing import List, Optional
import logging
import os

from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, ArgumentMultiline
from validation import ValidationManager
from file_access_policy import FileAccessPolicy
from selection_manager import SelectionManager


class WriteFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy,
               validation_manager: Optional[ValidationManager],
               selection_manager: SelectionManager):
    self.file_access_policy = file_access_policy
    self.validation_manager = validation_manager
    self.selection_manager = selection_manager

  def Name(self) -> str:
    return "write_file"

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        description="Writes the given content to a specified file.",
        required=[
            Argument(
                name="path",
                arg_type=ArgumentContentType.PATH_OUTPUT,
                description="The file path to write the content to.")
        ],
        multiline=ArgumentMultiline(
            required=True,
            description="The content to write into the specified file."))

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    if len(command_input.arguments) != 1 or not command_input.multiline_content:
      return CommandOutput(
          output=[],
          errors=[
              f"{self.Name()} expects exactly one argument: the file path and requires content."
          ],
          summary=f"{self.Name()} command failed due to incorrect arguments.")

    path = command_input.arguments[0]
    content: List[str] = command_input.multiline_content
    logging.info(f"Write: {path}")

    if not self.file_access_policy.allow_access(path):
      return CommandOutput(
          output=[],
          errors=[
              f"Access to '{path}' is not allowed. Only files in the current directory (and subdirectories) can be written to and must satisfy the access policy."
          ],
          summary=f"{self.Name()} command access denied.")

    selection_invalidated = False
    current_selection = self.selection_manager.get_selection()
    if current_selection and current_selection.path == path:
      self.selection_manager.clear_selection()
      selection_invalidated = True

    try:
      directory = os.path.dirname(path)
      if directory:
        os.makedirs(directory, exist_ok=True)

      with open(path, "w") as f:
        f.write("\n".join(content))
      if self.validation_manager:
        self.validation_manager.RegisterChange()

      line_count = len(content)
      output_msg = f"#{self.Name()} {path}: Success with {line_count} lines written."
      if selection_invalidated:
        output_msg += " Selection invalidated due to write operation on the same file."

      return CommandOutput(
          output=[output_msg],
          errors=[],
          summary=f"Wrote to file {path} with {line_count} lines.")
    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"Error writing to {path}: {str(e)}"],
          summary=f"{self.Name()} command encountered an error.")
