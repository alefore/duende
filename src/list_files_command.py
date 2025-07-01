from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
from typing import List, Tuple, Optional, Dict, Any
import logging
import os
from file_access_policy import FileAccessPolicy
from list_files import list_all_files


def _ListFileDetails(
    directory: str,
    file_access_policy: FileAccessPolicy) -> Tuple[List[str], List[str]]:
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
  return details, errors


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

  # TODO: Inline this into `run` and simplify (avoid unnecessary variables).
  def _process_directory(self,
                         directory: str) -> Tuple[List[str], List[str], str]:
    """
    Processes a single directory.
    Returns: (output_lines, errors, summary)
    """
    try:
      details, errors = _ListFileDetails(directory, self.file_access_policy)
      output_lines: list[str] = []
      if details:
        output_lines.extend(details)
      summary = (f"Listed files: '{directory}'. Matches: {len(details)}" +
                 (f", errors: {len(errors)}" if errors else ""))
      return output_lines, errors, summary
    except NotADirectoryError:
      error_msg = f"Directory not found or is not accessible: {directory}"
      summary = f"{self.Name()} command failed for '{directory}' due to inaccessible directory."
      return [], [error_msg], summary
    except Exception as e:
      error_msg = f"Listing files in {directory}: {e}"
      summary = f"{self.Name()} command encountered an error for '{directory}'."
      return [], [error_msg], summary

  def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    directory = inputs.get('directory', ["."])

    output_lines, errors, summary = self._process_directory(directory)

    return CommandOutput(
        output=output_lines,
        errors=errors,
        summary=summary,
        command_name=self.Name())
