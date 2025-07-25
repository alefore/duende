import os
from typing import AsyncIterator
from file_access_policy import FileAccessPolicy
import asyncio


async def list_all_files(directory: str,
                           file_access_policy: FileAccessPolicy) -> AsyncIterator[str]:
  """Generates all file paths in a directory and its subdirectories, filtered by the file access policy for output."""

  abs_directory = os.path.abspath(directory)
  if not os.path.isdir(abs_directory):
    raise NotADirectoryError(f"{directory} is not a valid directory.")

  # Run os.walk in a separate thread to avoid blocking the event loop
  for root, _, files in await asyncio.to_thread(os.walk, abs_directory):
    for file in sorted(files):
      file_path = os.path.join(root, file)
      if file_access_policy.allow_access(file_path):
        yield os.path.relpath(file_path, abs_directory)
