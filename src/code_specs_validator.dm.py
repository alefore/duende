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
    raise NotImplementedError()  # {{🍄 validator post init}}

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
    raise NotImplementedError()  # {{🍄 validator validate}}

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
    """
    raise NotImplementedError()  # {{🍄 implement validator}}
