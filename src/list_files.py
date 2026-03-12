import os
from typing import AsyncIterator
from file_access_policy import FileAccessPolicy
import asyncio
import pathlib
from enum import Enum, auto


class DirectoryBehavior(Enum):
  RECURSE = auto()
  NO_RECURSE = auto()


async def list_all_files(
    base_path: pathlib.Path,
    file_access_policy: FileAccessPolicy,
    directory_behavior: DirectoryBehavior = DirectoryBehavior.RECURSE
) -> AsyncIterator[pathlib.Path]:
  """Generates all file paths in a directory and its subdirectories, filtered by the file access policy for output."""

  if not base_path.is_dir():
    raise NotADirectoryError(f"{base_path} is not a valid directory.")

  # Use rglob to get all files and directories recursively
  # Run in a separate thread to avoid blocking the event loop
  match directory_behavior:
    case DirectoryBehavior.RECURSE:
      all_paths = await asyncio.to_thread(lambda: list(base_path.rglob("*")))
    case DirectoryBehavior.NO_RECURSE:
      all_paths = await asyncio.to_thread(lambda: list(base_path.glob("*")))

  # Sort paths for consistent output
  for file_path_obj in sorted(all_paths):
    if file_path_obj.is_file():
      if file_access_policy.allow_access(str(file_path_obj)):
        yield base_path / file_path_obj.relative_to(base_path)
