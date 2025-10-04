import aiofiles
import asyncio
import logging
import re
import pathlib
from typing import NamedTuple, NewType, Pattern, Sequence

from agent_loop import AgentLoop
from agent_loop_options import AgentLoopOptions
from conversation import Conversation, ConversationId, ConversationFactory
from message import Message, ContentSection
from conversation_state import ConversationState
from agent_workflow import AgentWorkflow, AgentWorkflowFactory, AgentWorkflowOptions
from agent_command import VariableMap, VariableName
from done_command import DoneValuesValidator
from validation import ValidationResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

implementation_variable = VariableName('implementation')


class DMAndValidator(NamedTuple):
  dm_path: pathlib.Path
  validator: str


MarkerName = NewType('MarkerName', str)


def _get_comment_char(path: pathlib.Path) -> str:
  """Returns the comment character based on the file extension (e.g., `#`).

  Supports these extensions: .py, .sh, .cc, .h"""
  # ✨ get comment char
  if path.suffix in ('.py', '.sh'):
    return '#'
  if path.suffix in ('.cc', '.h'):
    return '//'
  raise ValueError(f"Unknown file suffix: {path.suffix}")
  # ✨


def _validate_implementation_string(implementation: str,
                                    marker_name: MarkerName, comment_char: str):
  """raises ValueError if implementation lacks correct beginning+end lines."""
  # ✨ validate implementation string
  lines = implementation.strip().splitlines()
  if not lines:
    raise ValueError("Implementation cannot be empty.")

  expected_start = f"{comment_char} ✨ {marker_name}"
  expected_end = f"{comment_char} ✨"

  if lines[0] != expected_start:
    raise ValueError(f"Implementation must start with '{expected_start}', "
                     f"but got '{lines[0]}'")
  if lines[-1] != expected_end:
    raise ValueError(f"Implementation must end with '{expected_end}', "
                     f"but got '{lines[-1]}'")
  # ✨


async def _expand_marker(path: pathlib.Path, name: MarkerName,
                         implementation: str):
  """Rewrites `path`, replacing the marker `name` with an implementation.

  Raises an exception if `implementation` can't be validated; or if the marker
  doesn't occur exactly once in the file."""
  # ✨ expand marker
  comment_char = _get_comment_char(path)
  _validate_implementation_string(implementation, name, comment_char)

  async with aiofiles.open(path, mode='r') as f:
    file_content = await f.read()
  lines = file_content.splitlines()

  marker_to_find = f"{comment_char} {{🍄 {name}}}"
  marker_count = 0
  new_lines = []
  for line in lines:
    if marker_to_find in line:
      new_lines.extend(implementation.splitlines())
      marker_count += 1
    else:
      new_lines.append(line)

  if marker_count == 0:
    raise ValueError(f"Marker '{marker_to_find}' not found in file '{path}'")
  if marker_count > 1:
    raise ValueError(f"Marker '{marker_to_find}' found {marker_count} times "
                     f"in file '{path}'. Expected exactly one occurrence.")

  async with aiofiles.open(path, mode='w') as f:
    await f.write("\n".join(new_lines))
  # ✨


class DMValidator(DoneValuesValidator):

  def __init__(self, inputs: DMAndValidator, output_path: pathlib.Path,
               marker_name: MarkerName):
    self._validator = inputs.validator
    self._output_path = output_path
    self._marker_name = marker_name

  async def validate(self, inputs: VariableMap) -> ValidationResult:
    """Validates an implementation of the marker."""
    implementation = inputs[implementation_variable]
    assert isinstance(implementation, str)
    cmd_to_run = self._validator.format(
        **{'path': str(await self._expand_in_tmp_copy(implementation))})
    # ✨ run validation
    proc = await asyncio.create_subprocess_shell(
        cmd_to_run,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()

    success = proc.returncode == 0
    error = stderr.decode().strip()
    output = stdout.decode().strip()

    return ValidationResult(success=success, output=output, error=error)
    # ✨

  async def _expand_in_tmp_copy(self, implementation) -> pathlib.Path:
    """Makes a tmp copy of output_path, implementing marker_name."""
    return pathlib.Path()  # {{🍄 expand in tmp copy}}


class CodeSpecsWorkflow(AgentWorkflow):

  def __init__(self, options: AgentWorkflowOptions) -> None:
    self._options = options

  async def run(self) -> None:

    inputs = await self._get_initial_parameters()
    output_path = await self._prepare_output(inputs)
    relevant_files = await self._find_relevant_files(output_path)
    await self._implement_all_markers(inputs, output_path, relevant_files)

    logger.info("CodeSpecsWorkflow completed successfully.")

  async def _get_initial_parameters(self) -> DMAndValidator:
    """Ask the user for a valid DM file.

    Runs an AgentLoop asking the user for:

    1. The path to the file

    2. A command that can be used to validate an implementation of the file.
       This command must not contain the path to the file directly,
       but should have a `{path}` token that we'll expand (with `format`).

    The AgentLoop gives these parameters to the `done` command. The `done`
    command validates that the file is correct.
    """
    return DMAndValidator(pathlib.Path(), '')  # {{🍄 initial parameters }}

  async def _prepare_output(self, inputs: DMAndValidator) -> pathlib.Path:
    """Reats the DM file and prepares the output file.

    Prepends the "DO NOT EDIT" header at the top."""
    return pathlib.Path()  # {{🍄 prepare output }}

  async def _find_relevant_files(
      self, path: pathlib.Path) -> dict[MarkerName, set[pathlib.Path]]:
    """Finds all relevant files to implement each DM marker.

    To do this, for each marker in `path` starts an AgentLoop asking the
    Conversational AI to focus exclusively on the specific marker and to
    identify all the relevant files. The conversational AI should list all local
    files that may contain relevant information for an implementer of the
    marker. The conversational AI should give these paths as a parameter to the
    `done` command; `done` command verifies that these files all exist.

    These conversations are started concurrently.

    Returns:
      A dictionary containing all markers and their relevant files."""
    return {}  # {{🍄 find relevant files}}

  async def _implement_all_markers(
      self, inputs: DMAndValidator, output_path: pathlib.Path,
      relevant_files: dict[MarkerName, set[pathlib.Path]]) -> None:
    """Implements all DM markers.

    Starts a concurrent conversation for each DM marker. The conversation
    must call `done` to implement the marker, passing the implementation as
    required parameter `implementation_variable`."""
    # {{🍄 implement}}


class CodeSpecsWorkflowFactory(AgentWorkflowFactory):

  def name(self) -> str:
    return "code_specs_workflow"

  async def new(self, agent_workflow_options: AgentWorkflowOptions,
                args: dict[str, str]) -> AgentWorkflow:
    return CodeSpecsWorkflow(agent_workflow_options)