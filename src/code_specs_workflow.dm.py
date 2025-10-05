import aiofiles
import asyncio
import logging
import pathlib
import re
import shutil
import tempfile
from typing import NamedTuple, NewType, Pattern, Sequence

from agent_loop import AgentLoop
from agent_loop_options import AgentLoopOptions
from command_registry import CommandRegistry
from conversation import Conversation, ConversationId, ConversationFactory
from message import Message, ContentSection
from conversation_state import ConversationState
from agent_workflow import AgentWorkflow, AgentWorkflowFactory, AgentWorkflowOptions
from agent_command import Argument, ArgumentContentType, VariableMap, VariableName, VariableValue
from done_command import DoneCommand, DoneValuesValidator
from file_access_policy import FileAccessPolicy
from list_files_command import ListFilesCommand
from read_file_command import ReadFileCommand
from write_file_command import WriteFileCommand
from validation import ValidationResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

implementation_variable = VariableName('implementation')

# The local path to a DM file (including the `.dm.` part).
dm_path_variable = VariableName('dm_path')

# A shell command that can be used to validate that the output file (with some
# DM markers expanded) is correct. If the DM file being expanded contains unit
# tests, this typically just runs it.
validator_variable = VariableName('validator')

# A comma-separated list of local files that someone implementing a DM marker
# may want to have access to.
relevant_paths_variable = VariableName('relevant_paths')


class PathAndValidator(NamedTuple):
  dm_path: pathlib.Path
  validator: DMValidator


# A string with a shell command including the token `{path}`, which will be
# expanded (with `validator.format(…)`) to the path to be validated. Validation
# is successful if this command exits with 0.
DMValidator = NewType('DMValidator', str)

MarkerName = NewType('MarkerName', str)


def _get_comment_char(path: pathlib.Path) -> str:
  """Returns the comment character based on the file extension (e.g., `#`).

  Supported extensions: py, sh, cc, h, js, ts, java, css, html"""
  #  {{🍄 get comment char}}
  raise ValueError(f"Unknown file suffix: {path.suffix}")


class MarkerImplementation:

  def __init__(self, name: MarkerName, value: str) -> None:
    """Stores attributes and validates the format of `value`.

    Raises:
         ValueError if value lacks valid beginning and end comments."""
    raise NotImplementedError()  # {{🍄 marker implementation constructor}}

  # {{🍄 `name` and `value` getters}}

  async def save(self, path: pathlib.Path) -> None:
    """Rewrites `path`, storing our implementation.

    Raises:
        ValueError if the marker doesn't occur exactly once in `path`."""
    raise NotImplementedError()  # {{🍄 marker implementation save}}


async def _run_validator(path: pathlib.Path,
                         validator: DMValidator) -> ValidationResult:
  """Runs `validator` (expanding `path`), returning ValidationResult."""
  raise NotImplementedError()  # {{🍄 def run validator}}


async def _list_markers(path: pathlib.Path) -> set[MarkerName]:
  """Returns a list of all markers in `path`.

  Raises:
      ValueError if the file is not a valid DM file or the path does not include
      the `.dm.` suffix."""
  raise NotImplementedError()  # {{🍄 list markers}}


class CodeSpecsWorkflow(AgentWorkflow):

  def __init__(self, options: AgentWorkflowOptions) -> None:
    self._options = options

  async def run(self) -> None:

    inputs = await self._get_initial_parameters()
    output_path = await self._prepare_output(inputs)
    relevant_paths = await self._find_relevant_paths(output_path)
    await self._implement_file(inputs, output_path, relevant_paths)

    logger.info("CodeSpecsWorkflow completed successfully.")

  def _get_command_registry(self, arguments: list[Argument],
                            validator: DoneValuesValidator) -> CommandRegistry:
    """Creates a command registry with a `done` command expecting `arguments`.

    The registry includes only `read_file`, `list_files` and `done`."""
    raise NotImplementedError()  # {{🍄 get command registry}}

  async def _get_initial_parameters(self) -> PathAndValidator:
    """Ask the user for a valid DM file.

    Runs an AgentLoop where the user specifies values for dm_path_variable and
    validator_variable (given to `done` and validated).

    The starting message for the AgentLoop should instruct the conversational AI
    to prompt the user for the appropriate values. Something like:

    > Please ask the user (through text conversation) for approprivate values to
    > use for the variables expected by `done`. Once the user has given you
    > appropriate values, your goal is achieved and you should run `done`.
    """

    class DoneValidator(DoneValuesValidator):
      """Validates inputs given to `done`.

      Confirms that `inputs[dm_path_variable]` is a valid DM specs file and that
      `inputs[validator_variable]` …

      * … includes the string `{path}`
      * … successfully validates `inputs[dm_path_variable]`."""
      raise NotImplementedError()  # {{🍄 initial validator}}

    raise NotImplementedError  # {{🍄 initial parameters}}

  async def _prepare_output(self, inputs: PathAndValidator) -> pathlib.Path:
    """Reads the input DM file and prepares the output file.

    No markers are expanded. Prepends the "DO NOT EDIT" header at the top."""
    raise NotImplementedError()  # {{🍄 prepare output}}

  async def _find_relevant_paths(
      self, path: pathlib.Path) -> dict[MarkerName, set[pathlib.Path]]:
    """Finds all relevant files to implement each DM marker.

    Does it by starting concurrent conversations for all markers."""
    raise NotImplementedError()  # {{🍄 find relevant files loop}}

  async def _find_relevant_paths_marker(
      self, path: pathlib.Path, marker: MarkerName) -> set[pathlib.Path]:
    """Finds all relevant files to implement a single DM marker.

    Runs an AgentLoop focused exclusively on `marker`, to identify the
    approriate value for relevant_paths_variable."""

    class DoneValidator(DoneValuesValidator):
      """Verifies that all inputs[relevant_paths_variable] values are readable.

      Each path must:

      1. Be authorized by the file_access_policy.
      2. Be readable (not just exist, but confirm that it can be opened)."""
      raise NotImplementedError()  # {{🍄 relevant paths validator}}

    raise NotImplementedError()  # {{🍄 find relevant files}}

  async def _implement_file(
      self, inputs: PathAndValidator, output_path: pathlib.Path,
      relevant_paths: dict[MarkerName, set[pathlib.Path]]) -> None:
    """Implements all DM markers sequentially."""
    raise NotImplementedError()  # {{🍄 implement file}}

  async def _implement_marker(self, marker: MarkerName,
                              relevant_paths: set[pathlib.Path],
                              validator: DMValidator,
                              output_path: pathlib.Path) -> None:
    """Runs an AgentLoop and uses the output to implement `marker`.

    The AgentLoop is focused on `marker`. Instructs the AI to read all
    `relevant_paths` before doing anything else. The AI should then pass the
    implementation code to `done` (see `implementation_variable`).

    Once the `AgentLoop` returns, expands the marker in `output_path`."""

    class DoneValidator(DoneValuesValidator):
      """Validates implementation of marker on a tmp copy of output path."""
      raise NotImplementedError()  # {{🍄 implement validator}}

    raise NotImplementedError()  # {{🍄 implement all markers}}


class CodeSpecsWorkflowFactory(AgentWorkflowFactory):

  def name(self) -> str:
    return "code_specs_workflow"

  async def new(self, agent_workflow_options: AgentWorkflowOptions,
                args: dict[str, str]) -> AgentWorkflow:
    return CodeSpecsWorkflow(agent_workflow_options)
