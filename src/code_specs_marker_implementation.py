"""Implementation of a Duende block."""

import aiofiles
import pathlib

from code_specs import FileExtension, DuendeBlockName, comment_string, get_duende_blocks, reindent_code, DuendeBlockName


class DuendeBlockImplementation:

  def __init__(self, name: DuendeBlockName, value: str,
               file_extension: FileExtension) -> None:
    """Sets _name, _value, _file_extension from inputs.

    The value is the full implementation.

    Raises:
      ValueError unless `value` starts and ends with appropriate `✨` comments.
        Per doc/code-specs.md, these comments may contain leading whitespaces.
    """
    # ✨ marker implementation constructor
    self._name = name
    self._value = value
    self._file_extension = file_extension

    value_lines = [line for line in value.splitlines() if line.strip()]

    if not value_lines:
      raise ValueError("Implementation block cannot be empty.")

    # An implementation block must contain at least two non-empty lines:
    # one for the start marker and one for the end marker.
    if len(value_lines) < 2:
      raise ValueError(
          "Implementation block must have at least a start and end marker line."
      )

    first_line_stripped = value_lines[0].lstrip()
    last_line_stripped = value_lines[-1].lstrip()

    # Generate the expected start and end comment lines. We then strip any *inherent* leading
    # whitespace that the `comment_string` function itself might add (e.g., "  // " for C-style
    # comments). This allows the actual `value` lines to have arbitrary leading whitespace before
    # their comment characters.
    expected_start_comment_content = f"✨ {name}"
    expected_start_comment_line_template = comment_string(
        file_extension, expected_start_comment_content).lstrip()

    expected_end_comment_content = "✨"
    expected_end_comment_line_template = comment_string(
        file_extension, expected_end_comment_content).lstrip()

    if first_line_stripped != expected_start_comment_line_template:
      raise ValueError(
          f"Implementation block must start with appropriate '✨' comment. "
          f"Expected (stripped): '{expected_start_comment_line_template}', "
          f"Got (stripped): '{first_line_stripped}'")

    if last_line_stripped != expected_end_comment_line_template:
      raise ValueError(
          f"Implementation block must end with appropriate '✨' comment. "
          f"Expected (stripped): '{expected_end_comment_line_template}', "
          f"Got (stripped): '{last_line_stripped}'")
    # ✨

  # {{🦔 A call to MarkerImplementation.name returns the correct name}}
  # {{🦔 A call to MarkerImplementation.value returns the correct value}}
  # ✨ `name` and `value` getters
  @property
  def name(self) -> DuendeBlockName:
    return self._name

  @property
  def value(self) -> str:
    return self._value

  # ✨

  async def save(self, path: pathlib.Path) -> None:
    """Rewrites `path`, storing our implementation.

    {{🦔 The read operation is async.}}
    {{🦔 The write operation is async.}}
    {{🦔 Successfully expands a marker in a file with a single marker.}}
    {{🦔 Successfully expands a marker that spans multiple lines (i.e., that
         has newline characters in the name).}}
    {{🦔 Successfully expands the correct marker in a file with ten markers.}}
    {{🦔 The value is stored literally, without adding any leading spaces.}}
    {{🦔 The value written (the implementation) is reindented according to the
         rules of `_value_indent`; the number of desired spaces is equal to the
         number of spaces before the first non-space character in the line that
         contains the marker.}}
    {{🦔 Uses `get_duende_blocks` rather than redundantly implementing its
         logic.}}
    {{🦔 The file written ends in a newline character.}}

    Exceptions:

    {{🦔 Raises ValueError if the marker doesn't occur in `path`.
         The file is not modified.}}
    {{🦔 Raises ValueError if the marker occurs twice in `path`.
         The file is not modified.}}
    {{🦔 Raises FileNotFoundError for a non-existent file.}}
    """
    # ✨ marker implementation save
    # 1. Get marker positions.
    all_markers = await get_duende_blocks(path)
    matching_markers = [m for m in all_markers if m.name == self._name]
    if len(matching_markers) != 1:
      raise ValueError(
          f"Duende block '{self._name}' found {len(matching_markers)} times in '{path}'. Expected exactly one."
      )

    marker = matching_markers[0]
    marker_line_idx = marker.start_index

    # 2. Read the file content.
    async with aiofiles.open(
        path, mode='r') as f:
      lines = (await f.read()).splitlines()

    # 3. Determine the indentation of the marker line.
    marker_line = lines[marker_line_idx]
    indentation = len(marker_line) - len(marker_line.lstrip())

    # 4. Prepare the replacement content with correct indentation.
    indented_value = reindent_code(self._value, indentation)

    # 5. Reconstruct the file content.
    new_lines = []
    new_lines.extend(lines[:marker_line_idx])  # Lines before the marker
    new_lines.extend(indented_value.splitlines())  # Insert the implementation
    new_lines.extend(lines[marker_line_idx + 1:])  # Lines after the marker

    new_content = "\n".join(new_lines)

    # Ensure the file ends with a newline character if it's not empty
    if new_content and not new_content.endswith("\n"):
      new_content += "\n"

    # 6. Write the updated content back to the file.
    async with aiofiles.open(path, mode='w') as f:
      await f.write(new_content)
    # ✨
