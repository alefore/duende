from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
from typing import List, Optional
import logging
from file_access_policy import FileAccessPolicy
from list_files import list_all_files
import os


class SearchFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

  def Name(self) -> str:
    return "search"

  def GetDescription(self) -> str:
    return f"#{self.Name()} <content> [file1 file2 …]: Searches for the specific <content> in specified files (or in all files)."

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        required=[
            Argument(
                name="content",
                arg_type=ArgumentContentType.STRING,
                description="The content to search for")
        ],
        repeatable_final=Argument(
            name="file",
            arg_type=ArgumentContentType.PATH,
            description="Files to search in. If none is given, searches the entire repository."
        ))

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    if len(command_input.arguments) < 1:
      return CommandOutput(
          output=[],
          errors=[
              f"Invalid usage, expected: #{command_input.command_name} <search_term> [file1 file2 ...]"
          ],
          summary="Search command failed due to insufficient arguments.")

    search_term: str = command_input.arguments[0]
    specified_files: List[str] = command_input.arguments[1:] if len(
        command_input.arguments) > 1 else []
    logging.info(
        f"Searching for '{search_term}' in specified files or directory and subdirectories."
    )

    matches = []
    errors: List[str] = []

    global_file_count = 0
    global_line_count = 0
    global_match_count = 0

    files_to_search = specified_files or list_all_files(".",
                                                        self.file_access_policy)

    files_data: List[str] = []

    match_limit = 200
    for file_path in files_to_search:
      try:
        global_file_count += 1
        with open(file_path, 'r', encoding='utf-8') as file:
          lines = file.readlines()
          file_line_count: int = len(lines)
          global_line_count += file_line_count

        file_match_count = 0
        for i, line in enumerate(lines):
          if search_term in line:
            file_match_count += 1
            global_match_count += 1
            if global_match_count < match_limit:
              matches.append(f"{file_path}:{i + 1}: {line.strip()}")

        if file_match_count > 0:
          files_data.append(
              f"{file_path}, {file_match_count}, {file_line_count}")

      except Exception as e:
        errors.append(f"{file_path}: {str(e)}")

    header = f"Files searched: {global_file_count}, Lines scanned: {global_line_count}, Matches found: {global_match_count}"
    if global_match_count > match_limit:
      csv_content = "path,lines_match,file_line_count\n"
      csv_content += "\n".join(files_data)

      output = (
          f"Too many matches to display ({global_match_count}, limit is {match_limit}). {header}.\n"
          f"Files with matches:\n{csv_content}")
    else:
      output = header + "\n" + ("\n".join(matches) if matches else
                                f"No matches found for '{search_term}'.")

    summary = f"Searched {global_file_count} files, found {global_match_count} matches."
    if errors:
      summary += f" Errors: {len(errors)}"
    return CommandOutput(output=[output], errors=errors, summary=summary)
