from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
from typing import List, Tuple, Optional, Dict, Any
import logging
import os
from file_access_policy import FileAccessPolicy
from list_files import list_all_files


def _ListFileDetails(directory: str,
                     file_access_policy: FileAccessPolicy) -> Tuple[str, str]:
  details: List[str] = []
  errors: List[str] = []
  for file in list_all_files(directory, file_access_policy):
    file_path = os.path.join(directory, file)
    try:
      with open(file_path, 'r') as f:
        lines = f.readlines()
        line_count = len(lines)
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
                name="directory",
                arg_type=ArgumentContentType.PATH_UNVALIDATED,
                description="The directory path to list files from.",
                required=False)
        ])

  def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    directory = inputs.get('directory', ".")

    try:
      output, errors = _ListFileDetails(directory, self.file_access_policy)

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
