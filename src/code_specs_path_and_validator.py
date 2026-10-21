import aiofiles
import dataclasses
import pathlib

from code_specs import FileExtension, MarkerChar, RepeatedDuendeBlocksError, comment_string, get_duende_blocks
from code_specs_validator import Validator


@dataclasses.dataclass(frozen=True)
class PathAndValidator:
  """An immutable container for a file path and a validator."""
  path: pathlib.Path
  validator: Validator

  async def validate_fields(self) -> None:
    """Validates fields, conditionally raising ValueError.

    {{🦔 Doesn't raise if `path` is a valid file with two duende blocks.}}
    {{🦔 Raises ValueError if `path` contains a repeated duende block.}}
    {{🦔 Raises ValueError if `path` doesn't contain any duende blocks.}}

    We can't use `__post_init__` because we want `async` validation.
    """
    # ✨ PathAndValidator validate fields
    try:
      blocks = await get_duende_blocks(self.path)
    except RepeatedDuendeBlocksError as e:
      raise ValueError(
          f"Repeated duende blocks found in '{self.path}': {e}") from e
    except FileNotFoundError as e:
      raise ValueError(f"File not found: '{self.path}'") from e

    if not blocks:
      raise ValueError(f"No duende blocks found in '{self.path}'.")

    # ✨

  def file_extension(self) -> FileExtension:
    """Returns the file extension of the `path`.

    {{🦔 For `path` "foo/bar/quux.py", returns "py"}}
    """
    # ✨ PathAndValidator file extension
    return FileExtension(self.path.suffix.lstrip('.'))
    # ✨

  def old_path(self) -> pathlib.Path:
    """Returns the "old" path, where the previous implementation is backed up.

    This is done by replacing the ".dm." part with ".old.".

    When expansion begins, we use these paths to make a copy of previous files
    that we'll overwrite.

    {{🦔 For `path` "foo/bar.py", returns "foo/bar.old.py".}}
    """
    # ✨ PathAndValidator old path
    ext = self.file_extension()
    return pathlib.Path(self.path.parent /
                        self.path.name.replace(ext, f".old.{ext}"))
    # ✨

  async def copy_to(self, target: pathlib.Path) -> None:
    """Copies `path`'s contents to `target` (overwriting it).

    {{🦔 The read operation is async}}
    {{🦔 The write operation is async}}
    {{🦔 The output of a call with a normal file contains a copy.}}
    """
    # ✨ overwrite
    async with aiofiles.open(
        self.path, mode='r') as f:
      content = await f.read()

    async with aiofiles.open(target, mode='w') as f:
      await f.write(content)
    # ✨
