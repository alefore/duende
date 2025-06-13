from agent_command import AgentCommand, CommandInput
from typing import List
import logging
from file_access_policy import FileAccessPolicy
from list_files import list_all_files


class ListFilesCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

  def GetDescription(self) -> str:
    return "#list_files [directory]: Lists all files in the given directory or the current directory if none is specified."

  def Execute(self, command_input: CommandInput) -> str:
    if len(command_input.arguments) > 1:
      return f"Error: {command_input.command_name} expects at most one argument: the directory path."

    directory = command_input.arguments[0] if command_input.arguments else "."
    logging.info(f"Listing files in directory: {directory}")

    try:
      files = list_all_files(directory, self.file_access_policy)
      return f"Files in '{directory} <<':\n" + "\n".join(
          files) + f"\n#end ({directory})\n"
    except NotADirectoryError:
      return f"Error: Directory not found or is not accessible: {directory}"
    except Exception as e:
      return f"Error: Listing files in {directory}: {e}"
