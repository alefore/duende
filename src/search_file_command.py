from agent_command import AgentCommand, CommandInput
from typing import List, Optional
import logging
from file_access_policy import FileAccessPolicy
from list_files import list_all_files

# TODO: If more than 200 lines match, don't return any individual matches;
# instead, return a header describing this, including the total number of
# matches. Then return a CSV file like this: path, lines_match, total_lines.
# (Include a header so that the AI knows how to interpret this).


class SearchFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

  def GetDescription(self) -> str:
    return "SearchFileCommand: Searches for a specific term in specified files (if provided) or in all files in the current directory and subdirectories."

  def Execute(self, command_input: CommandInput) -> str:
    if len(command_input.arguments) < 1:
      return f"Error: Invalid usage, expected: #{command_input.command_name} <search_term> [file1 file2 ...]"

    search_term: str = command_input.arguments[0]
    specified_files: List[str] = command_input.arguments[1:] if len(
        command_input.arguments) > 1 else []
    logging.info(
        f"Searching for '{search_term}' in specified files or directory and subdirectories."
    )

    matches = []
    errors = []

    file_count = 0
    line_count = 0
    match_count = 0

    files_to_search = specified_files or list_all_files(".",
                                                        self.file_access_policy)

    for file_path in files_to_search:
      try:
        file_count += 1
        with open(file_path, 'r', encoding='utf-8') as file:
          lines = file.readlines()
          line_count += len(lines)

        for i, line in enumerate(lines):
          if search_term in line:
            matches.append(f"{file_path}:{i + 1}: {line.strip()}")
            match_count += 1

      except Exception as e:
        errors.append(f"{file_path}: {str(e)}")

    header = f"Files searched: {file_count}, Lines scanned: {line_count}, Matches found: {match_count}"
    result = header + "\n" + ("\n".join(matches) if matches else
                              f"No matches found for '{search_term}'.")

    if errors:
      result += "\n\nSome files raised exceptions:\n" + "\n".join(errors)

    return result
