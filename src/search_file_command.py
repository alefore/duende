from agent_command import AgentCommand
from typing import List
import logging
from file_access_policy import FileAccessPolicy
from list_files import list_all_files


class SearchFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

  def GetDescription(self) -> str:
    return "SearchFileCommand: Searches for a specific term in all files in the current directory and subdirectories."

  # TODO: Execute is incorrect! It should receive a CommandInput rather than
  # a list of strings!
  def Execute(self, arguments: List[str]) -> str:
    if len(arguments) != 1:
      return "Usage: #search_file <search_term>"

    search_term = arguments[0]
    logging.info(
        f"Searching for '{search_term}' in directory and subdirectories.")

    try:
      matches = []
      for file_path in list_all_files(".", self.file_access_policy):
        with open(file_path, 'r') as file:
          lines = file.readlines()

        for i, line in enumerate(lines):
          if search_term in line:
            matches.append(f"{file_path}:{i + 1}: {line.strip()}")

      if matches:
        return "\n".join(matches)
      else:
        return f"No matches found for '{search_term}'."

    except Exception as e:
      return f"Error: {str(e)}"
