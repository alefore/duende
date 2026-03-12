import aiofiles
import asyncio
import logging
import pathlib
import os
from typing import AsyncIterable, Iterable, Any

from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, PATH_VARIABLE_NAME, REASON_VARIABLE, VariableName, VariableMap, VariableValue
from file_access_policy import FileAccessPolicy
from list_files import list_all_files
from pathbox import PathBox


def _collect_errors(errors: list[str]) -> str:
  """Returns a string with the first 10 errors.

  {{🦔 If more than 10 errors are found, includes a string like:
       "(348 errors omitted)".}}
  """
  raise NotImplementedError()  # {{🍄 collect errors}}


class SearchFileCommand(AgentCommand):

  def __init__(self, cwd: PathBox, file_access_policy: FileAccessPolicy):
    self._cwd = cwd
    self.file_access_policy = file_access_policy

  def Name(self) -> str:
    return self.Syntax().name

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        name="search_file",
        description="Searches for the specific content.",
        arguments=[
            REASON_VARIABLE,
            Argument(
                name=VariableName("content"),
                arg_type=ArgumentContentType.STRING,
                description="The content to search for.",
                required=True),
            Argument(
                name=PATH_VARIABLE_NAME,
                arg_type=ArgumentContentType.PATH_INPUT,
                description="File to search in. Skip it to find references in the entire repository.",
                required=False),
            Argument(
                name=VariableName("case_sensitive"),
                arg_type=ArgumentContentType.BOOL,
                description="If true, the match must be case sensitive (false by default).",
                required=False)
        ])

  def _get_paths_to_search(
      self, input_path: pathlib.Path | None) -> AsyncIterable[pathlib.Path]:
    if not input_path:
      return list_all_files(self._cwd.path, self.file_access_policy)
    elif pathlib.Path(input_path).is_dir():
      return list_all_files(self._cwd / input_path, self.file_access_policy)
    else:
      # If a specific file path is provided,
      # convert it to an async iterable for consistency
      async def _single_file_iterator() -> AsyncIterable[pathlib.Path]:
        yield input_path

      return _single_file_iterator()

  async def run(self, inputs: VariableMap) -> CommandOutput:
    search_term: str = str(inputs[VariableName("content")]).strip()
    input_path: VariableValue | None = inputs.get(VariableName("path"))
    assert isinstance(input_path, pathlib.Path | None)

    if len(search_term.splitlines()) > 1:
      raise NotImplementedError()  # {{🍄 return error pattern crosses lines}}

    logging.info(
        f"Searching for '{search_term}' in specified files or directory and subdirectories."
    )

    matches = []
    errors: list[str] = []

    global_file_count = 0
    global_line_count = 0
    global_match_count = 0

    paths_to_search = self._get_paths_to_search(input_path)

    files_data: list[str] = []

    match_limit = 100
    async for file_path in paths_to_search:
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
              matches.append(f"{file_path}:{i + 1}: {line.strip()}")

        if file_match_count > 0:
          files_data.append(
              f"{file_path}, {file_match_count}, {file_line_count}")

      except Exception as e:
        errors.append(f"{file_path}: {str(e)}")

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

    summary = f"Searched {global_file_count} files, found {global_match_count} matches."
    if errors:
      summary += f" Errors: {len(errors)}"
    return CommandOutput(
        output=output_str,
        errors=_collect_errors(errors),
        summary=summary,
        command_name=self.Syntax().name)
