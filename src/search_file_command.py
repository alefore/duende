from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, VariableName
from typing import AsyncIterable, Iterable, Dict, Any
import logging
from file_access_policy import FileAccessPolicy
from list_files import list_all_files
import os
import aiofiles
import asyncio
import pathlib  # Added import


class SearchFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

  def Name(self) -> str:
    return self.Syntax().name

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        name="search_file",
        description="Searches for the specific content.",
        arguments=[
            Argument(
                name=VariableName("content"),
                arg_type=ArgumentContentType.STRING,
                description="The content to search for",
                required=True),
            Argument(
                name=VariableName("path"),
                arg_type=ArgumentContentType.PATH_INPUT,
                description="File to search in. Skip it to find references in the entire repository.",
                required=False)
        ])

  async def run(self, inputs: Dict[VariableName, Any]) -> CommandOutput:
    search_term: str = inputs[VariableName("content")]
    input_path: str | None = inputs.get(VariableName("path"))
    logging.info(
        f"Searching for '{search_term}' in specified files or directory and subdirectories."
    )

    matches = []
    errors: list[str] = []

    global_file_count = 0
    global_line_count = 0
    global_match_count = 0

    paths_to_search: AsyncIterable[str]

    if not input_path:
      paths_to_search = list_all_files(".", self.file_access_policy)
    elif pathlib.Path(input_path).is_dir():
      paths_to_search = list_all_files(input_path, self.file_access_policy)
    else:
      # If a specific file path is provided,
      # convert it to an async iterable for consistency
      async def _single_file_iterator() -> AsyncIterable[str]:
        yield input_path

      paths_to_search = _single_file_iterator()

    files_data: list[str] = []

    match_limit = 200
    async for file_path_str in paths_to_search:
      file_path = pathlib.Path(file_path_str)

      try:
        global_file_count += 1
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
          lines = await file.readlines()
          file_line_count: int = len(lines)
          global_line_count += file_line_count

        file_match_count = 0
        for i, line in enumerate(lines):
          if search_term in line:
            file_match_count += 1
            global_match_count += 1
            if global_match_count < match_limit:
              matches.append(f"{file_path_str}:{i + 1}: {line.strip()}")

        if file_match_count > 0:
          files_data.append(
              f"{file_path_str}, {file_match_count}, {file_line_count}")

      except Exception as e:
        errors.append(f"{file_path_str}: {str(e)}")

    output_lines: list[str] = [
        f"Files searched: {global_file_count}, Lines scanned: {global_line_count}, Matches found: {global_match_count}"
    ]

    if global_match_count > match_limit:
      output_lines.extend([
          f"Too many matches to display ({global_match_count}, limit is {match_limit}).",
          "Files with matches:",
          "path,lines_match,file_line_count",
      ])
      output_str = "\n".join(output_lines + files_data)
    elif matches:
      output_str = "\n".join(output_lines + matches)
    else:
      output_str = "\n".join(output_lines +
                             [f"No matches found for '{search_term}'."])

    errors_str = "\n".join(errors)

    summary = f"Searched {global_file_count} files, found {global_match_count} matches."
    if errors:
      summary += f" Errors: {len(errors)}"
    return CommandOutput(
        output=output_str,
        errors=errors_str,
        summary=summary,
        command_name=self.Syntax().name)
