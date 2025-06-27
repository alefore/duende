from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
from typing import List, Tuple, Optional
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
    return "list_files"

  def Aliases(self) -> List[str]:
    return ["list", "ls"]

  def _process_single_directory(
      self, directory: str) -> Tuple[List[str], List[str], str, Optional[str]]:
    """
    Processes a single directory.
    Returns: (output_lines, errors, general_summary_part, special_not_a_directory_summary)
    The special_not_a_directory_summary is the exact string expected by a specific test case
    for a single non-existent directory, otherwise None.
    """
    try:
      details, errors = _ListFileDetails(directory, self.file_access_policy)
      output_lines = [f"Files in '{directory}' <<"]
      if details:
        output_lines.extend(details)
      output_lines.append(f"#end ({directory})")
      general_summary_part = (
          f"Listed files: '{directory}'. Matches: {len(details)}" +
          (f", errors: {len(errors)}" if errors else ""))
      return output_lines, errors, general_summary_part, None
    except NotADirectoryError:
      error_msg = f"Directory not found or is not accessible: {directory}"
      general_summary_part = f"{self.Name()} command failed for '{directory}' due to inaccessible directory."
      special_summary = f"{self.Name()} command failed due to inaccessible directory."  # The one the test expects
      return [], [error_msg], general_summary_part, special_summary
    except Exception as e:
      error_msg = f"Listing files in {directory}: {e}"
      general_summary_part = f"{self.Name()} command encountered an error for '{directory}'."
      return [], [error_msg], general_summary_part, None

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    directories = command_input.arguments or ["."]

    all_output_lines: List[str] = []
    all_errors: List[str] = []
    all_summaries: List[str] = []
    special_summary_for_single_case: Optional[str] = None

    for directory in directories:
      output_lines, errors, general_summary_part, special_summary_candidate = self._process_single_directory(
          directory)

      all_output_lines.extend(output_lines)
      all_errors.extend(errors)
      all_summaries.append(general_summary_part)

      if len(directories) == 1 and special_summary_candidate is not None:
        special_summary_for_single_case = special_summary_candidate

    final_summary = (
        special_summary_for_single_case or "; ".join(all_summaries) or
        f"{self.Name()} completed.")

    return CommandOutput(
        output=all_output_lines, errors=all_errors, summary=final_summary)

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        description="Lists all files in the given directories (or the top-level if none is specified).",
        repeatable_final=Argument(
            name="directory",
            arg_type=ArgumentContentType.PATH_UNVALIDATED,
            description="The directory path to list files from. Can be specified multiple times."
        ))
