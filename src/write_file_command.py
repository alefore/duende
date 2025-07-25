from typing import Any, Dict, List, Optional
import logging
import os
import difflib

from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
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
    return self.Syntax().name

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        name="write_file",
        description="Writes the given content to a specified file.",
        arguments=[
            Argument(
                name="path",
                arg_type=ArgumentContentType.PATH_OUTPUT,
                description="The file path to write the content to."),
            Argument(
                name="content",
                arg_type=ArgumentContentType.STRING,
                description="The content to write."),
            Argument(
                name="reason",
                arg_type=ArgumentContentType.STRING,
                description="Brief (one or two sentences) explanation of why you are issuing this command (what you want to accomplish).",
                required=False)
        ],
        output_description='A string describing the result of the operation, possibly including a diff.'
    )

  def _get_full_diff(self, path: str, new_content: str) -> Optional[List[str]]:
    if not os.path.exists(path):
      return None

    with open(path, "r") as f:
      original_content_lines: List[str] = f.read().splitlines()
    diff = list(
        difflib.unified_diff(
            original_content_lines,
            new_content.splitlines(),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            lineterm="",
        ))
    return diff

  def derive_args(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
    output = {}
    if inputs['path'] and inputs['content']:
      output['content_diff'] = self._derive_diff(inputs['path'],
                                                 inputs['content'])
    return output

  def _derive_diff(self, path: str, new_content: str) -> str:
    try:
      diff = self._get_full_diff(path, new_content)
      if diff is None:
        return "File is new."
      elif not diff:
        return "No changes."
      else:
        return "\n".join(diff)
    except Exception as e:
      return f"Could not compute diff: {e}"

  def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    path = inputs['path']
    new_content = inputs['content']
    logging.info(f"Write: {path}")

    selection_invalidated = False
    current_selection = self.selection_manager.get_selection()
    if current_selection and current_selection.path == path:
      self.selection_manager.clear_selection()
      selection_invalidated = True

    try:
      directory = os.path.dirname(path)
      if directory:
        os.makedirs(directory, exist_ok=True)

      diff = self._get_full_diff(path, new_content)

      with open(path, "w") as f:
        f.write(new_content)
      if self.validation_manager:
        self.validation_manager.RegisterChange()

      new_content_lines = new_content.splitlines()
      output_messages = [
          f"#{self.Name()} {path}: Success with {len(new_content_lines)} lines written."
      ]
      if selection_invalidated:
        output_messages[
            0] += " Selection invalidated due to write operation on the same file."

      if diff is None:
        output_messages.append("File is new.")
      elif not diff:
        output_messages.append("No changes.")
      elif 0 < len(diff) < 25:
        output_messages.append("```diff")
        output_messages.extend(diff)
        output_messages.append("```")
      elif len(diff) >= 25:
        added = sum(1 for line in diff
                    if line.startswith('+') and not line.startswith('++'))
        removed = sum(1 for line in diff
                      if line.startswith('-') and not line.startswith('--'))
        output_messages.append(
            f"Diff is too large. Summary: {added} lines added, {removed} lines removed."
        )

      return CommandOutput(
          output="\n".join(output_messages),
          errors="",
          summary=f"Wrote to file {path} with {len(new_content_lines)} lines.",
          command_name=self.Name())
    except Exception as e:
      return CommandOutput(
          output="",
          errors=f"Error writing to {path}: {str(e)}",
          summary=f"{self.Name()} command encountered an error.",
          command_name=self.Name())
