"""Implementation of workflow to expand DM markers per doc/code-specs.md."""

import aiofiles
import asyncio
import dataclasses
import logging
import pathlib
import re
import shutil
import subprocess
import tempfile
from typing import NamedTuple, NewType, Pattern, Sequence

from agent_loop_options import AgentLoopOptions
from agent_loop_options import BaseAgentLoopFactory
from command_registry import CommandRegistry
from conversation import Conversation, ConversationId, ConversationFactory
from message import Message, ContentSection
from conversation_state import ConversationState
from agent_workflow import AgentWorkflow, AgentWorkflowFactory
from agent_workflow_options import AgentWorkflowOptions
from agent_command import Argument, ArgumentContentType, VariableMap, VariableName, VariableValue
from done_command import DoneCommand, DoneValuesValidator
from file_access_policy import FileAccessPolicy
from list_files_command import ListFilesCommand
from read_file_command import ReadFileCommand
from write_file_command import WriteFileCommand
from validation import ValidationResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A string with a shell command including the token `{path}`, which will be
# expanded (with `validator.format(…)`) to the path to be validated. Validation
# is successful if this command exits with 0. If the DM file being expanded
# contains unit tests, this typically just runs it. Should be able to validate
# copies on /tmp of input files.
DMValidator = NewType('DMValidator', str)


class PathAndValidatorError(ValueError):
  """Base class for errors related to PathAndValidator validation."""


class NoMarkersFoundError(PathAndValidatorError):
  """No markers were found."""


class RepeatedMarkersFoundError(PathAndValidatorError):
  """Repeated (identical) DM markers were found."""


class ValidatorTemplateError(PathAndValidatorError):
  """A DMValidator doesn't include a {path} placeholder."""


@dataclasses.dataclass(frozen=True)
class _PathAndValidator:
  """An immutable container for a DM file path and a validator.

  Attributes:
    dm_path: The local path to a DM file (including the `.dm.` part). Must be a
             valid file containing DM markers and they must not be repeated.
    validator: The validator to use.
  """
  dm_path: pathlib.Path
  validator: DMValidator

  def __post_init__(self):
    """Raises PathAndValidatorError if something is wrong."""
    #  {{🍄 PathAndValidator post init}}


# If the end user specifies files with globs (e.g., `src/bar/*/age*/fo*.py`),
# the conversational AI should try to expand it and help the user.
dm_path_variable = VariableName('dm_path')

validator_variable = VariableName('validator')

# Value is a block of code that implement a DM marker.
implementation_variable = VariableName('implementation')

# Value is a comma-separated list of local files that someone implementing a DM
# marker may want to read.
relevant_paths_variable = VariableName('relevant_paths')

MarkerName = NewType('MarkerName', str)


def _comment_string(file_extension: str, input: str) -> str:
  """Turns `input` into a valid code comment based on `path`'s extension.

  Example: _comment_string('html', 'bar') returns '<!-- bar -->'.

  Supported extensions: py, sh, cc, h, js, ts, java, html, css
  """
  #  {{🍄 get comment char}}
  raise ValueError(f"Unknown file extension: {file_extension}")


class _MarkerImplementation:

  def __init__(self, name: MarkerName, value: str, file_extension: str) -> None:
    """Sets _name, _value, _file_extension from inputs.

    Raises:
      ValueError if value lacks beginning and end comments (matching name).
    """
    raise NotImplementedError()  # {{🍄 marker implementation constructor}}

  # {{🍄 `name` and `value` getters}}

  async def save(self, path: pathlib.Path) -> None:
    """Rewrites `path`, storing our implementation.

    Raises:
        ValueError if the marker doesn't occur exactly once in `path`."""
    raise NotImplementedError()  # {{🍄 marker implementation save}}


async def _run_validator(path: pathlib.Path,
                         validator: DMValidator) -> ValidationResult:
  """Runs `validator` (after expanding `{path}` to path)."""
  raise NotImplementedError()  # {{🍄 def run validator}}


async def _list_markers(path: pathlib.Path) -> list[MarkerName]:
  """Returns all markers in `path` in appearance order.

  Raises:
      ValueError if the file does not contain any markers or contains repeated
      markers."""
  raise NotImplementedError()  # {{🍄 list markers}}


async def _run_agent_loop(self, agent_loop_factory: BaseAgentLoopFactory,
                          conversation_name: str, start_message_content: str,
                          done_command: DoneCommand) -> VariableMap:
  """Creates and runs a BaseAgentLoop.

    The new conversation has: ReadFileCommand, ListFilesCommand, done_command.

    Args:
      agent_loop_factory: The factory used to create the BaseAgentLoop.
      conversation_name: The name for the conversation that will be created.
      start_message_content: The initial prompt (for start_message).
      done_command: The `done` command to use, allowing customers to control
        (1) which variables are expected, and (2) how to validate state.

    Returns:
      Output variables given to the final `done` command (extracted from the
      final message in the conversation).
    """
  raise NotImplementedError()  # {{🍄 run agent loop}}


class CodeSpecsWorkflow(AgentWorkflow):

  def __init__(self, options: AgentWorkflowOptions) -> None:
    self._options = options

  async def run(self) -> None:
    inputs = await self._get_initial_parameters()
    output_path = await self._prepare_output(inputs)
    relevant_paths = await self._find_relevant_paths(output_path)
    await self._implement_file(inputs, output_path, relevant_paths)

    logger.info("CodeSpecsWorkflow completed successfully.")

  async def _get_initial_parameters(self) -> _PathAndValidator:
    """Obtains values to initialize a _PathAndValidator.

    Calls `_run_agent_loop` passing a done_command with `arguments` matching
    `dm_path_variable` and `validator_variable`. The starting message is this:

    > Ask the user (through text conversation) for approprivate values for the
    > variables expected by `done`. Describe these variables to the user to help
    > them understand what is expected.
    >
    > Once the user has given you appropriate values, your goal is achieved and
    > you should run `done`.
    """

    class DoneValidator(DoneValuesValidator):
      """Validates that a _PathAndValidator can be created from `inputs`.

      If _PathAndValidator(…) raises an exception, gives a friendly error
      message to the AI."""
      raise NotImplementedError()  # {{🍄 initial parameters validator}}

    raise NotImplementedError  # {{🍄 initial parameters}}

  async def _prepare_output(self, inputs: _PathAndValidator) -> pathlib.Path:
    """Reads the input DM file and prepares the output file.

    No markers are expanded. Prepends the "DO NOT EDIT …" header at the top."""
    raise NotImplementedError()  # {{🍄 prepare output}}

  async def _find_relevant_paths(
      self, path: pathlib.Path) -> dict[MarkerName, set[pathlib.Path]]:
    """Concurrently calls find_relevant_paths_marker for all markers."""
    raise NotImplementedError()  # {{🍄 find relevant paths loop}}

  async def _find_relevant_paths_marker(
      self, path: pathlib.Path, marker: MarkerName) -> set[pathlib.Path]:
    """Finds all relevant paths to implement a single DM marker.

    Runs an AgentLoop focused exclusively on `marker`, to identify the
    approriate value for relevant_paths_variable.
    """

    class DoneValidator(DoneValuesValidator):
      """Verifies that all inputs[relevant_paths_variable] values are readable.

      The files must be readable, and file_access_policy must allow access.
      """
      raise NotImplementedError()  # {{🍄 relevant paths validator}}

    raise NotImplementedError()  # {{🍄 find relevant paths}}

  async def _implement_file(
      self, inputs: _PathAndValidator, output_path: pathlib.Path,
      relevant_paths: dict[MarkerName, set[pathlib.Path]]) -> None:
    """Implements all DM markers sequentially."""
    raise NotImplementedError()  # {{🍄 implement file}}

  async def _implement_marker(self, marker: MarkerName,
                              relevant_paths: set[pathlib.Path],
                              validator: DMValidator,
                              output_path: pathlib.Path) -> None:
    """Runs an AgentLoop and uses the output to implement `marker`.

    The AgentLoop is focused on `marker`. Tells the AI to read all
    `relevant_paths` *and* `output_path` before doing anything else. The AI
    must pass the implementation code to `done` (see `implementation_variable`).
    The prompt given to the AI is crafted carefully, to explain how it must
    infer the desired intent from `output_path`.

    Once the `AgentLoop` returns, saves the implementation in `output_path`."""

    class DoneValidator(DoneValuesValidator):
      """Validates implementation of marker on a tmp copy of `output_path`."""
      raise NotImplementedError()  # {{🍄 implement validator}}

    raise NotImplementedError()  # {{🍄 implement single marker}}


class CodeSpecsWorkflowFactory(AgentWorkflowFactory):

  def name(self) -> str:
    return "code_specs_workflow"

  async def new(self, agent_workflow_options: AgentWorkflowOptions,
                args: dict[str, str]) -> AgentWorkflow:
    return CodeSpecsWorkflow(agent_workflow_options)
