from typing import Any, Dict
import logging
import os
import difflib
import aiofiles
import asyncio

from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, VariableName
from validation import ValidationManager
from selection_manager import SelectionManager

_content_variable = VariableName("content")


class WriteFileCommand(AgentCommand):

  def __init__(self, validation_manager: ValidationManager | None,
               selection_manager: SelectionManager,
               hard_coded_path: str | None):
    self.validation_manager = validation_manager
    self.selection_manager = selection_manager
    self._hard_coded_path = hard_coded_path

  def Name(self) -> str:
    return self.Syntax().name

  def _optional_arguments(self) -> list[Argument]:
    if self._hard_coded_path:
      return []
    return [
        Argument(
            name=VariableName("path"),
            arg_type=ArgumentContentType.PATH_OUTPUT,
            description="The file path to write the content to."),
        Argument(
            name=VariableName("reason"),
            arg_type=ArgumentContentType.STRING,
            description="Brief (one or two sentences) explanation of why you are issuing this command (what you want to accomplish).",
            required=False)
    ]

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name=VariableName("write_file"),
        description="Writes the given content to a specified file.",
        arguments=[
            Argument(
                name=_content_variable,
                arg_type=ArgumentContentType.STRING,
                description="The content to write.")
        ] + self._optional_arguments(),
        output_description='A string describing the result of the operation, possibly including a diff.'
    )

  async def _get_full_diff(self, path: str,
                           new_content: str) -> list[str] | None:
    if not await asyncio.to_thread(os.path.exists, path):
      return None

    async with aiofiles.open(path, "r") as f:
      original_content_lines: list[str] = (await f.read()).splitlines()
    diff = list(
        difflib.unified_diff(
            original_content_lines,
            new_content.splitlines(),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            lineterm="",
        ))
    return diff

  async def derive_args(
      self, inputs: dict[VariableName, Any]) -> dict[VariableName, Any]:
    output: dict[VariableName, Any] = {}
    path = self._hard_coded_path or inputs.get(VariableName("path"))
    if path and inputs.get(_content_variable):
      output[VariableName("content_diff")] = await self._derive_diff(
          path, inputs[_content_variable])
    return output

  async def _derive_diff(self, path: str, new_content: str) -> str:
    try:
      diff = await self._get_full_diff(path, new_content)
      if diff is None:
        return "File is new."
      elif not diff:
        return "No changes."
      else:
        return "\n".join(diff)
    except Exception as e:
      return f"Could not compute diff: {e}"

  async def run(self, inputs: Dict[VariableName, Any]) -> CommandOutput:
    path = self._hard_coded_path or inputs[VariableName("path")]
    new_content = inputs[_content_variable]
    logging.info(f"Write: {path}")

    selection_invalidated = False
    current_selection = self.selection_manager.get_selection()
    if current_selection and current_selection.path == path:
      self.selection_manager.clear_selection()
      selection_invalidated = True

    try:
      directory = os.path.dirname(path)
      if directory:
        await asyncio.to_thread(os.makedirs, directory, exist_ok=True)

      diff = await self._get_full_diff(path, new_content)

      async with aiofiles.open(path, mode="w") as f:
        await f.write(new_content)
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
          command_name=self.Name(),
          task_done=bool(self._hard_coded_path))
    except Exception as e:
      return CommandOutput(
          output="",
          errors=f"Error writing to {path}: {str(e)}",
          summary=f"{self.Name()} command encountered an error.",
          command_name=self.Name())
