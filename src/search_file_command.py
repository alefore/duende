from agent_command import AgentCommand, CommandInput
from typing import List
import logging
from file_access_policy import FileAccessPolicy
from list_files import list_all_files


class SearchFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

  def GetDescription(self) -> str:
    return "SearchFileCommand: Searches for a specific term in all files in the current directory and subdirectories."

  def Execute(self, command_input: CommandInput) -> str:
    if len(command_input.arguments) != 1:
      return f"Error: Invalid usage, expected: #{command_input.command_name} <search_term>"

    search_term = command_input.arguments[0]
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
