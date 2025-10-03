from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, VariableName
from typing import List, Tuple, Dict, Any
import logging
import os
import aiofiles

from file_access_policy import FileAccessPolicy
from list_files import list_all_files


async def _ListFileDetails(
    directory: str, file_access_policy: FileAccessPolicy) -> Tuple[str, str]:
  details: List[str] = []
  errors: List[str] = []
  async for file in list_all_files(directory, file_access_policy):
    file_path = os.path.join(directory, file)
    try:
      async with aiofiles.open(file_path, 'r') as f:
        lines = await f.readlines()
        line_count = len(lines)
        # os.path.getsize is synchronous, should be fine for now, or use aiofiles.os.stat
        byte_count = os.path.getsize(file_path)
        details.append(f"{file}: {line_count} lines, {byte_count} bytes")
    except Exception as e:
      errors.append(f"Error: {file}: Error reading: {str(e)}")
  return "\n".join(details), "\n".join(errors)


class ListFilesCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

  def Name(self) -> str:
    return self.Syntax().name

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        name="list_files",
        description="Lists all files in the given directories (or the top-level if none is specified).",
        arguments=[
            Argument(
                name=VariableName("directory"),
                arg_type=ArgumentContentType.PATH_UNVALIDATED,
                description="The directory path to list files from.",
                required=False)
        ])

  async def run(self, inputs: Dict[VariableName, Any]) -> CommandOutput:
    directory = inputs.get(VariableName("directory"), ".")

    try:
      output, errors = await _ListFileDetails(directory,
                                              self.file_access_policy)

      return CommandOutput(
          output=output,
          errors=errors,
          summary=(
              f"Listed files: '{directory}'. Matches: {len(output.splitlines() if output else [])}"
              + (f", errors: {len(errors.splitlines() if errors else [])}"
                 if errors else "")),
          command_name=self.Name())
    except NotADirectoryError:
      return CommandOutput(
          output="",
          errors=f"Directory not found or is not accessible: {directory}",
          summary=f"{self.Name()} command failed for '{directory}' due to inaccessible directory.",
          command_name=self.Name())
    except Exception as e:
      return CommandOutput(
          output="",
          errors=f"Listing files in {directory}: {e}",
          summary=f"{self.Name()} command encountered an error for '{directory}'.",
          command_name=self.Name())
