"""Supporting logic for DM-related workflows.md."""

import aiofiles
import pathlib

from code_specs import FileExtension, MarkerName, comment_string, get_markers, reindent_code


class MarkerImplementation:

  def __init__(self, name: MarkerName, value: str,
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
    expected_start_comment_content = f"✨ {name.name}"
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
  def name(self) -> MarkerName:
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
    {{🦔 Raises ValueError if the marker doesn't occur in `path`}}
    {{🦔 Raises ValueError if the marker occurs twice in `path`}}
    {{🦔 Raises FileNotFoundError for a non-existent file.}}
    {{🦔 Raises ValueError if `path` contains a ".dm." part}}
    {{🦔 The value written (the implementation) is reindented according to the
         rules of `_value_indent`; the number of desired spaces is equal to the
         number of spaces before the first non-space character in the line that
         contains the marker.}}
    {{🦔 Uses `get_markers` rather than redundantly implementing its logic.}}

    Raises:
      ValueError if `path` has a `.dm.` part. DM files themselves should never
      be updated.
    """
    # ✨ marker implementation save
    if ".dm." in path.name:
      raise ValueError(
          f"`path` ('{path}') must not contain '.dm.'. DM files themselves should never be updated."
      )

    # 1. Get marker positions.
    all_markers = await get_markers(self._name.char, path)
    if self._name not in all_markers:
      raise ValueError(
          f"Marker '{{{{{str(self._name.char)} {self._name.name}}}}}' found 0 times in '{path}'. Expected exactly one."
      )
    if len(all_markers[self._name]) > 1:
      raise ValueError(
          f"Marker '{{{{{str(self._name.char)} {self._name.name}}}}}' found {len(all_markers[self._name])} times in '{path}'. Expected exactly one."
      )

    marker_line_idx = all_markers[self._name][0]

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

    # 6. Write the updated content back to the file.
    async with aiofiles.open(
        path, mode='w') as f:
      await f.write(new_content)
    # ✨
