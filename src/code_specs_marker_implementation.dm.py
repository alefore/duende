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
    raise NotImplementedError()  # {{🍄 marker implementation constructor}}

  # {{🦔 A call to MarkerImplementation.name returns the correct name}}
  # {{🦔 A call to MarkerImplementation.value returns the correct value}}
  # {{🍄 `name` and `value` getters}}

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
    {{🦔 Uses `get_markers` rather than redundantly implementing its logic.}}
    {{🦔 The file written ends in a newline character.}}

    Exceptions:

    {{🦔 Raises ValueError if the marker doesn't occur in `path`.
         The file is not modified.}}
    {{🦔 Raises ValueError if the marker occurs twice in `path`.
         The file is not modified.}}
    {{🦔 Raises FileNotFoundError for a non-existent file.}}
    {{🦔 Raises ValueError if `path` contains a ".dm." part. The file is not
         modifies.}}

    Raises:
      ValueError if `path` has a `.dm.` part. DM files themselves should never
      be updated.
    """
    raise NotImplementedError()  # {{🍄 marker implementation save}}
