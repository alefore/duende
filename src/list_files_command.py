import logging
import os
import aiofiles
import pathlib

from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, REASON_VARIABLE, VariableMap, VariableName
from file_access_policy import FileAccessPolicy
from list_files import DirectoryBehavior, list_all_files
from pathbox import PathBox

_RECURSIVE_VARIABLE_NAME = VariableName("recursive")


async def _ListFileDetails(
    directory: pathlib.Path, file_access_policy: FileAccessPolicy,
    directory_behavior: DirectoryBehavior) -> tuple[str, str]:
  details: list[str] = []
  errors: list[str] = []
  async for file_path in list_all_files(directory, file_access_policy,
                                        directory_behavior):
    try:
      async with aiofiles.open(file_path, 'r') as f:
        lines = await f.readlines()
        line_count = len(lines)
        # os.path.getsize is synchronous, should be fine for now, or use aiofiles.os.stat
        byte_count = os.path.getsize(file_path)
        details.append(f"{file_path}: {line_count} lines, {byte_count} bytes")
    except Exception as e:
      errors.append(f"Error: {file_path}: Error reading: {str(e)}")
  return "\n".join(details), "\n".join(errors)


class ListFilesCommand(AgentCommand):

  def __init__(self, cwd: PathBox, file_access_policy: FileAccessPolicy):
    self._cwd = cwd
    self.file_access_policy = file_access_policy

  def Name(self) -> str:
    return self.Syntax().name

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        name="list_files",
        description="Lists all files in the given directories (or the top-level if none is specified).",
        arguments=[
            REASON_VARIABLE,
            Argument(
                name=VariableName("directory"),
                arg_type=ArgumentContentType.PATH_UNVALIDATED,
                description="The directory path to list files from.",
                required=False),
            Argument(
                name=_RECURSIVE_VARIABLE_NAME,
                arg_type=ArgumentContentType.BOOL,
                description="Should we recursively list subdirectories? (Default: false).",
                required=False)
        ])

  async def run(self, inputs: VariableMap) -> CommandOutput:
    directory_str = inputs.get(VariableName("directory"), ".")
    assert isinstance(directory_str, str)
    directory = self._cwd / pathlib.Path(directory_str)
    recursive = inputs.get(_RECURSIVE_VARIABLE_NAME, False)
    assert isinstance(recursive, bool)

    try:
      output, errors = await _ListFileDetails(
          directory, self.file_access_policy, DirectoryBehavior.RECURSE
          if recursive else DirectoryBehavior.NO_RECURSE)

      return CommandOutput(
          output=output,
          errors=errors,
          summary=(
              f"Listed files: '{directory}'. Matches: {len(output.splitlines() if output else [])}"
              + (f", errors: {len(errors.splitlines() if errors else [])}"
                 if errors else "")),
          command_name=self.Name())
    except NotADirectoryError:
      return CommandOutput(
          output="",
          errors=f"Directory not found or is not accessible: {directory}",
          summary=f"{self.Name()} command failed for '{directory}' due to inaccessible directory.",
          command_name=self.Name())
    except Exception as e:
      return CommandOutput(
          output="",
          errors=f"Listing files in {directory}: {e}",
          summary=f"{self.Name()} command encountered an error for '{directory}'.",
          command_name=self.Name())
