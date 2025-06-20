from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
from typing import List, Tuple
import logging
import os
from file_access_policy import FileAccessPolicy
from list_files import list_all_files


def _ListFileDetails(directory,
                     file_access_policy) -> Tuple[List[str], List[str]]:
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

  def GetDescription(self) -> str:
    return f"#{self.Name()} [directory]: Lists all files in the given directory (or the top-level if none is specified)."

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    if len(command_input.arguments) > 1:
      return CommandOutput(
          output=[],
          errors=[
              f"{self.Name()} expects at most one argument: the directory path."
          ],
          summary=f"Failed to execute {self.Name()} command due to incorrect argument count."
      )

    directory = command_input.arguments[0] if command_input.arguments else "."

    try:
      details, errors = _ListFileDetails(directory, self.file_access_policy)
      return CommandOutput(
          output=[
              f"Files in '{directory} <<':\n" + "\n".join(details) +
              f"\n#end ({directory})\n"
          ],
          errors=["\n".join(errors)],
          summary=(f"Listed files: '{directory}'. Matches: {len(details)}" +
                   (f", errors: {len(errors)}" if errors else "")))
    except NotADirectoryError:
      return CommandOutput(
          output=[],
          errors=[f"Directory not found or is not accessible: {directory}"],
          summary=f"{self.Name()} command failed due to inaccessible directory."
      )
    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"Listing files in {directory}: {e}"],
          summary=f"{self.Name()} command encountered an error.")

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        description="Lists all files in the given directory (or the top-level if none is specified).",
        optional=[
            Argument(
                name="directory",
                arg_type=ArgumentContentType.PATH_INPUT,
                description="The directory path to list files from.")
        ])
