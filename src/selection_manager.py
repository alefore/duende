from typing import List, Optional
import os


class Selection:

  def __init__(self, path: str, start_line_content: str,
               end_line_content: str) -> None:
    self.path = path
    self.start_line_content = start_line_content
    self.end_line_content = end_line_content
    self.selected_lines: List[str] = []

  def Read(self) -> List[str]:
    """Reads corresponding lines from the file and returns them."""
    if not os.path.exists(self.path):
      raise FileNotFoundError(f"File not found: {self.path}")

    with open(self.path, "r") as file:
      lines: List[str] = file.readlines()

    start_index = end_index = None
    for index, line in enumerate(lines):
      if start_index is None and self.start_line_content in line:
        start_index = index
      elif start_index is not None and self.end_line_content in line:
        end_index = index
        break

    if start_index is None:
      raise ValueError("Could not find the specified start line content.")
    if end_index is None:
      raise ValueError("Could not find the specified end line content.")

    self.selected_lines = lines[start_index:end_index + 1]
    return self.selected_lines

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

    start_index = None
    for index, line in enumerate(lines):
      if self.start_line_content in line:
        start_index = index
        break

    if start_index is None:
      raise ValueError("Could not find the specified start line content.")

    end_index = None
    for index in range(start_index, len(lines)):
      if self.end_line_content in lines[index]:
        end_index = index
        break

    if end_index is None:
      raise ValueError("Could not find the specified end line content.")

    # Replace lines between start_index and end_index
    new_contents_with_newlines = [f"{line}\n" for line in new_contents]
    lines = lines[:start_index] + new_contents_with_newlines + lines[end_index +
                                                                     1:]

    with open(self.path, "w") as file:
      file.writelines(lines)


class SelectionManager:

  def __init__(self) -> None:
    self.current_selection: Optional[Selection] = None

  def get_selection(self) -> Optional[Selection]:
    return self.current_selection

  def set_selection(self, selection: Selection) -> None:
    self.current_selection = selection

  def clear_selection(self) -> None:
    self.current_selection = None
