import asyncio
import dataclasses
import logging
import os
import pathlib
import shutil
import tempfile

from code_specs import MarkerChar, MarkersOverlapError, get_markers_str
from code_specs_marker_implementation import MarkerImplementation
from validation import ValidationResult


@dataclasses.dataclass(frozen=True)
class Validator:
  """A shell command that validates contents of a file.

  The command receives the path through $DMPATH. It should be able to validate
  copies on /tmp of input files (i.e., must not assume that it is always run in
  some particular directory).

  Validation is successful if the command exits with 0. If the DM file being
  implemented contains unit tests, this typically just runs it.
  """
  command: str

  def __post_init__(self) -> None:
    """Raises ValueError if the command doesn't include the string "DMPATH".

    {{🦔 Raises for incorrect string: "MYPYPATH=foo mypy {path}"}}
    {{🦔 Raises for incorrect string: "MYPYPATH=foo mypy $DM_PATH"}}
    {{🦔 Doesn't raise for "MYPYPATH=foo mypy $DMPATH"}}
    """
    # ✨ validator post init
    if "DMPATH" not in self.command:
      raise ValueError("Validator command must include 'DMPATH'.")
    # ✨

  async def validate_path(self, dm_path: pathlib.Path) -> ValidationResult:
    """Runs `command` on `dm_path` to validate it.

    {{🦔 Returns failure for "false # $DMPATH"}}
    {{🦔 Returns success for "true # $DMPATH"}}
    {{🦔 Correctly passes `dm_path` through the `DMPATH` env variable}}
    {{🦔 Command `TEST=foo sh -c 'test "$TEST" = "foo"' # $DMPATH` succeeds.
         This validates that we can actually processes shell syntax.}}
    """
    env = os.environ.copy()
    env['DMPATH'] = str(dm_path)
    # ✨ validator validate
    try:
      process = await asyncio.create_subprocess_exec(
          "/bin/bash",
          "-c",
          self.command,
          env=env,
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE,
      )
      stdout, stderr = await process.communicate()
      return ValidationResult(
          success=process.returncode == 0,
          output=stdout.decode().strip(),
          error=stderr.decode().strip())
    except Exception as e:
      logging.error(f"Error executing validator command: {str(e)}")
      return ValidationResult(success=False, output="", error=str(e))
    # ✨

  async def validate_marker_implementation(
      self, source: pathlib.Path,
      implementation: MarkerImplementation) -> ValidationResult:
    """Validates the implementation of a marker on a copy of `source`.

    {{🦔 Validation fails if the implementation contains markers (per
         `get_markers(MUSHROOM, …)`). In this case, a helpful string is
         returned, proposing an alternative along the lines of
         `"{{" + "🍄 …}}"` (which is enough to avoid this).}}
    {{🦔 The read operation is async}}
    {{🦔 The write operation is async}}
    {{🦔 Does not modify `source`}}
    {{🦔 Returns success when the implementation is correct}}
    {{🦔 Returns failure when the implementation is invalid}}
    {{🦔 Uses `implementation.save` on the temporary copy of `source` (in order
         to update the implementation of the marker in the file).}}
    {{🦔 The temporary copy of `source` is made asynchronously.}}
    """
    # ✨ implement validator
    # New validation: check for mushroom markers in the implementation content.
    try:
      mushroom_markers = get_markers_str(MarkerChar('🍄'), implementation.value)
      if mushroom_markers:
        marker_names = ", ".join(
            f"'{{{{🍄 {name.name}}}}}'" for name in mushroom_markers.keys())
        return ValidationResult(
            success=False,
            output="",
            error=(
                f"Implementation contains mushroom markers: {marker_names}. "
                "Please remove them or escape them like `'…{{' + '🍄 …}}…'`."))
    except MarkersOverlapError as e:
      return ValidationResult(
          success=False,
          output="",
          error=(f"Implementation contains overlapping markers: {e}. "))

    with tempfile.TemporaryDirectory() as tmpdir:
      temp_source_path = pathlib.Path(tmpdir) / source.name
      shutil.copy(source, temp_source_path)
      await implementation.save(temp_source_path)
      return await self.validate_path(temp_source_path)
    # ✨
