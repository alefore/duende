from agent_command import AgentCommand, CommandInput
from typing import List, Optional
import logging
from file_access_policy import FileAccessPolicy
from list_files import list_all_files
import os


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

    csv_data = []

    match_limit = 200  # Define a limit for the number of matches
    for file_path in files_to_search:
      try:
        file_count += 1
        with open(file_path, 'r', encoding='utf-8') as file:
          lines = file.readlines()
          file_lines_total = len(lines)
          line_count += file_lines_total

        file_matches = 0
        for i, line in enumerate(lines):
          if search_term in line:
            file_matches += 1
            match_count += 1
            if match_count < match_limit:
              matches.append(f"{file_path}:{i + 1}: {line.strip()}")

        if file_matches > 0:
          csv_data.append([file_path, file_matches, file_lines_total])

      except Exception as e:
        errors.append(f"{file_path}: {str(e)}")

    if match_count > match_limit:
      # Construct CSV data as a string
      csv_content = "path,lines_match,file_lines_total\n"
      csv_content += "\n".join([",".join(map(str, row)) for row in csv_data])

      result = (f"Files searched: {file_count}, Lines scanned: {line_count}, "
                f"Matches found: {match_count}. Too many matches to display. "
                f"Files with matches:\n{csv_content}")
    else:
      header = f"Files searched: {file_count}, Lines scanned: {line_count}, Matches found: {match_count}"
      result = header + "\n" + ("\n".join(matches) if matches else
                                f"No matches found for '{search_term}'.")

    if errors:
      result += "\n\nSome files raised exceptions:\n" + "\n".join(errors)

    return result
