from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
from typing import Iterable, List, Optional, Dict, Any
import logging
from file_access_policy import FileAccessPolicy
from list_files import list_all_files
import os


class SearchFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

  def Name(self) -> str:
    return self.Syntax().name

  def Aliases(self) -> List[str]:
    return ["find", "grep"]

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        name="search_file",
        description="Searches for the specific content.",
        arguments=[
            Argument(
                name="content",
                arg_type=ArgumentContentType.STRING,
                description="The content to search for",
                required=True),
            Argument(
                name="path",
                arg_type=ArgumentContentType.PATH_INPUT,
                description="File to search in. Skip it to find references in the entire repository.",
                required=False)
        ])

  def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    search_term: str = inputs['content']
    input_path: Optional[str] = inputs.get('path')
    logging.info(
        f"Searching for '{search_term}' in specified files or directory and subdirectories."
    )

    matches = []
    errors: List[str] = []

    global_file_count = 0
    global_line_count = 0
    global_match_count = 0

    paths_to_search: Iterable[str] = [input_path
                                     ] if input_path else list_all_files(
                                         ".", self.file_access_policy)

    files_data: List[str] = []

    match_limit = 200
    for file_path in paths_to_search:
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

    output_lines: List[str] = [
        f"Files searched: {global_file_count}, Lines scanned: {global_line_count}, Matches found: {global_match_count}"
    ]

    if global_match_count > match_limit:
      output_lines.extend([
          f"Too many matches to display ({global_match_count}, limit is {match_limit}).",
          "Files with matches:",
          "path,lines_match,file_line_count",
      ])
      output_lines.extend(files_data)
    elif matches:
      output_lines.extend(matches)
    else:
      output_lines.append(f"No matches found for '{search_term}'.")

    summary = f"Searched {global_file_count} files, found {global_match_count} matches."
    if errors:
      summary += f" Errors: {len(errors)}"
    return CommandOutput(
        output=output_lines,
        errors=errors,
        summary=summary,
        command_name=self.Syntax().name)
