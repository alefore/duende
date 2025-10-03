import os
import re
import aiofiles
import asyncio


class StartPatternNotFound(ValueError):
  pass


class EndPatternNotFound(ValueError):
  pass


class Selection:

  def __init__(self, path: str, start_index: int, end_index: int) -> None:
    self.path = path
    self.start_index = start_index
    self.end_index = end_index

  async def Read(self) -> list[str]:
    """Reads corresponding lines from the file and returns them."""
    if not await asyncio.to_thread(os.path.exists, self.path):
      raise FileNotFoundError(f"File not found: {self.path}")

    async with aiofiles.open(self.path, "r") as file:
      lines: list[str] = [l.rstrip('\n') for l in await file.readlines()]

    if self.start_index < 0 or self.end_index >= len(lines):
      raise ValueError("Start or end index out of range.")

    return lines[self.start_index:self.end_index + 1]

  async def Overwrite(self, new_contents: str) -> None:
    """
    Replaces the selection with new contents (deleting previous contents).
    The file (self.path) will be updated on disk.
    """
    if not await asyncio.to_thread(os.path.exists, self.path):
      raise FileNotFoundError(f"File not found: {self.path}")

    async with aiofiles.open(self.path, "r") as file:
      lines = (await file.readlines())

    if self.start_index < 0 or self.end_index >= len(lines):
      raise ValueError("Start or end index out of range.")

    # Replace lines between start_index and end_index
    lines = lines[:self.start_index] + [new_contents + '\n'] + lines[self.end_index + 1:]

    async with aiofiles.open(self.path, "w") as file:
      await file.writelines(lines)

  @classmethod
  async def FromLinePattern(cls, path: str, start_line_pattern: str,
                      end_line_pattern: str | None) -> 'Selection':
    """Creates a Selection object based on line patterns using regex.
    If end_line_pattern is None, only the start line is selected."""
    if not await asyncio.to_thread(os.path.exists, path):
      raise FileNotFoundError(f"File not found: {path}")

    async with aiofiles.open(path, "r") as file:
      lines: list[str] = await file.readlines()

    start_index = None
    for index, line in enumerate(lines):
      if start_index is None and re.search(start_line_pattern, line):
        start_index = index
        if end_line_pattern is None:
          return cls(path, start_index, start_index)
      elif start_index is not None and end_line_pattern is not None and re.search(
          end_line_pattern, line):
        return cls(path, start_index, index)

    if start_index is None:
      raise StartPatternNotFound()
    if end_line_pattern is not None:
      raise EndPatternNotFound()
    raise ValueError("Unexpected error in pattern matching.")

  def ProvideSummary(self) -> str:
    """Provides a summary of the selection made."""
    line_count = self.end_index - self.start_index + 1
    return f"Selected from {self.path}: {line_count} lines."


class SelectionManager:

  def __init__(self) -> None:
    self.current_selection: Selection | None = None

  def get_selection(self) -> Selection | None:
    return self.current_selection

  def set_selection(self, selection: Selection) -> None:
    self.current_selection = selection

  def clear_selection(self) -> None:
    self.current_selection = None
