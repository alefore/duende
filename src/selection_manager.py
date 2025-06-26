from typing import List, Optional
import os
import re


class StartPatternNotFound(ValueError):
  pass


class EndPatternNotFound(ValueError):
  pass


class Selection:

  def __init__(self, path: str, start_index: int, end_index: int) -> None:
    self.path = path
    self.start_index = start_index
    self.end_index = end_index

  def Read(self) -> List[str]:
    """Reads corresponding lines from the file and returns them."""
    if not os.path.exists(self.path):
      raise FileNotFoundError(f"File not found: {self.path}")

    with open(self.path, "r") as file:
      lines: List[str] = [l.rstrip('\n') for l in file.readlines()]

    if self.start_index < 0 or self.end_index >= len(lines):
      raise ValueError("Start or end index out of range.")

    return lines[self.start_index:self.end_index + 1]

  def Overwrite(self, new_contents: List[str]):
    """
    Replaces the selection with new contents (deleting previous contents).
    'new_contents' should not include newline characters at the end of each line.
    The file (self.path) will be updated on disk.
    """
    if not os.path.exists(self.path):
      raise FileNotFoundError(f"File not found: {self.path}")

    with open(self.path, "r") as file:
      lines = file.readlines()

    if self.start_index < 0 or self.end_index >= len(lines):
      raise ValueError("Start or end index out of range.")

    # Replace lines between start_index and end_index
    new_contents_with_newlines = [f"{line}\n" for line in new_contents]
    lines = lines[:self.start_index] + new_contents_with_newlines + lines[
        self.end_index + 1:]

    with open(self.path, "w") as file:
      file.writelines(lines)

  @classmethod
  def FromLinePattern(cls, path: str, start_line_pattern: str,
                      end_line_pattern: Optional[str]) -> 'Selection':
    """Creates a Selection object based on line patterns using regex.
    If end_line_pattern is None, only the start line is selected."""
    if not os.path.exists(path):
      raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r") as file:
      lines: List[str] = file.readlines()

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
    self.current_selection: Optional[Selection] = None

  def get_selection(self) -> Optional[Selection]:
    return self.current_selection

  def set_selection(self, selection: Selection) -> None:
    self.current_selection = selection

  def clear_selection(self) -> None:
    self.current_selection = None
