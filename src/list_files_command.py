from agent_command import AgentCommand, CommandInput, CommandOutput
from typing import List
import logging
from file_access_policy import FileAccessPolicy
from list_files import list_all_files


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
      files = list(list_all_files(directory, self.file_access_policy))
      return CommandOutput(
          output=[
              f"Files in '{directory} <<':\n" + "\n".join(files) +
              f"\n#end ({directory})\n"
          ],
          errors=[],
          summary=f"Listed files in directory '{directory}', matches: {len(files)}"
      )
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
