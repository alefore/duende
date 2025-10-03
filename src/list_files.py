import os
from typing import AsyncIterator
from file_access_policy import FileAccessPolicy
import asyncio
import pathlib


async def list_all_files(
    directory: str, file_access_policy: FileAccessPolicy) -> AsyncIterator[str]:
  """Generates all file paths in a directory and its subdirectories, filtered by the file access policy for output."""

  base_path = pathlib.Path(directory)
  if not base_path.is_dir():
    raise NotADirectoryError(f"{directory} is not a valid directory.")

  # Use rglob to get all files and directories recursively
  # Run in a separate thread to avoid blocking the event loop
  all_paths = await asyncio.to_thread(lambda: list(base_path.rglob('*')))

  # Sort paths for consistent output
  for file_path_obj in sorted(all_paths):
    if file_path_obj.is_file():
      if file_access_policy.allow_access(str(file_path_obj)):
        yield str(base_path / file_path_obj.relative_to(base_path))
