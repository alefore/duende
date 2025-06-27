from typing import List, Optional
import logging
import os
import difflib

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

  def Aliases(self) -> List[str]:
    return ["write", "edit", "edit_file", "replace", "replace_file"]

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

    path = command_input.arguments[0]
    assert command_input.multiline_content is not None, "Multiline content is required by CommandSyntax but was not provided."
    new_content_lines = command_input.multiline_content
    logging.info(f"Write: {path}")

    selection_invalidated = False
    current_selection = self.selection_manager.get_selection()
    if current_selection and current_selection.path == path:
      self.selection_manager.clear_selection()
      selection_invalidated = True

    try:
      original_content_lines = []
      if os.path.exists(path):
        with open(path, "r") as f:
          original_content_lines = f.read().splitlines()

      directory = os.path.dirname(path)
      if directory:
        os.makedirs(directory, exist_ok=True)

      with open(path, "w") as f:
        for line in new_content_lines:
          f.write(f"{line}\n")
      if self.validation_manager:
        self.validation_manager.RegisterChange()

      line_count = len(new_content_lines)
      output_messages = [f"#{self.Name()} {path}: Success with {line_count} lines written."]
      if selection_invalidated:
        output_messages[0] += " Selection invalidated due to write operation on the same file."

      diff = list(
          difflib.unified_diff(
              original_content_lines,
              new_content_lines,
              fromfile=f"a/{path}",
              tofile=f"b/{path}",
              lineterm="",
          ))

      if 0 < len(diff) < 25:
        output_messages.append("```diff")
        output_messages.extend(diff)
        output_messages.append("```")
      elif len(diff) >= 25:
        added = sum(1 for line in diff if line.startswith('+') and not line.startswith('++'))
        removed = sum(1 for line in diff if line.startswith('-') and not line.startswith('--'))
        output_messages.append(f"Diff is too large. Summary: {added} lines added, {removed} lines removed.")

      return CommandOutput(
          output=output_messages,
          errors=[],
          summary=f"Wrote to file {path} with {line_count} lines.")
    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"Error writing to {path}: {str(e)}"],
          summary=f"{self.Name()} command encountered an error.")
