"""Implementation of workflow to implement DM markers per doc/code-specs.md."""

import aiofiles
import asyncio
import dataclasses
import logging
import pathlib
import re
import os
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
from search_file_command import SearchFileCommand
from write_file_command import WriteFileCommand
from validation import ValidationResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A FileExtension like "py" or "html".
FileExtension = NewType("FileExtension", str)

MUSHROOM = "🍄"


def _comment_string(file_extension: FileExtension, input: str) -> str:
  """Turns `input` into a valid code comment based on `path`'s extension.

  Supported extensions: py, sh, cc, h, js, ts, java, html, css

  {{🌱 "py" and "foo bar" returns "# foo bar"}}
  {{🌱 "html" and "my test" returns "<!-- my test -->}}
  """
  #  {{🍄 get comment char}}
  raise ValueError(f"Unknown file extension: {file_extension}")


# _marker_pattern is a regex that can be used (with `re.search`) to find code
# lines that contain a DM marker: "{{" + "🍄" + an arbitrary name (which may
# contain spaces, such as "test method foo") + "}}". The first match group
# captures the name,  with leading/trailing spaces stripped away. Must be
# applied to individual lines (i.e., not to the whole file).
#
# {{🌱 Matches "      {{" + MUSHROOM + " foo}}"}}
# {{🌱 Matches "    raise Foo()   # {{" + MUSHROOM + " foo}} trailing blah"}}
# {{🌱 Doesn't match space after 🍄: "{{ " + MUSHROOM + "foo}}"}}
# {{🌱 Doesn't match random line "  if (kobolds_found) {""}}
_marker_pattern = re.compile(r'...')  #  {{🍄 marker pattern}}


@dataclasses.dataclass(frozen=True)
class _Validator:
  """A shell command that validates contents of a file.

  The command receives the path through $DMPATH. It should be able to validate
  copies on /tmp of input files (i.e., must not assume that it is always run in
  some particular directory).

  Validation is successful if the command exits with 0. If the DM file being
  implemented contains unit tests, this typically just runs it.
  """
  command: str

  def __post_init__(self):
    """Raises ValueError if the command doesn't include the string "DMPATH."""
    # {{🌱 Raises for incorrect string: "MYPYPATH=foo mypy {path}"}}
    # {{🌱 Raises for incorrect string: "MYPYPATH=foo mypy $DM_PATH"}}
    # {{🌱 Doesn't raise for "MYPYPATH=foo mypy $DMPATH"}}
    raise NotImplementedError()  # {{🍄 validator post init}}

  async def validate_path(self, dm_path: pathlib.Path) -> ValidationResult:
    # {{🌱 Returns failure for "false # $DMPATH"}}
    # {{🌱 Returns success for "true # $DMPATH"}}
    # {{🌱 Correctly passes `dm_path` through the `DMPATH` env variable}}
    env = os.environ.copy()
    env['DMPATH'] = str(dm_path)
    raise NotImplementedError()  # {{🍄 validator validate}}


async def _get_markers(path: pathlib.Path) -> list[MarkerName]:
  """Returns all markers in `path` in appearance order.

  `path` is read asynchronously.

  Raises:
      ValueError if the file does not contain any markers or contains repeated
      markers. The message contains a specific and detailed description.
  """
  # {{🌱 Reads `path` asynchronously}}
  # {{🌱 Raises ValueError for an empty file}}
  # {{🌱 Raises FileNotFound for a non-existent file}}
  # {{🌱 Raises ValueError for a file with 5 lines but no markers}}
  # {{🌱 Correctly returns a marker in a file with just 1 marker}}
  # {{🌱 Spaces are correctly removed from a marker named "  foo bar  "}}
  # {{🌱 Returns all markers in a file with ten markers}}
  # {{🌱 The order of markers returned in a file with ten markers is correct.}}
  raise NotImplementedError()  # {{🍄 list markers}}


@dataclasses.dataclass(frozen=True)
class _PathAndValidator:
  """An immutable container for a DM file path and a validator."""
  dm_path: pathlib.Path
  validator: _Validator

  async def validate_fields(self):
    """Validates fields, conditionally raising ValueError.

    {{🌱 Doesn't raise if `dm_path` is a valid file with two markers}}
    {{🌱 Raises ValueError if `dm_path` is "foo.py"}}
    {{🌱 Raises ValueError if `dm_path` is a valid Python file with no markers}}
    {{🌱 Raises ValueError if `dm_path` contains a repeated marker}}

    We can't use `__post_init__` because we want `async` validation.
    """
    # {{🍄 PathAndValidator validate fields}}

  async def prepare_output(self) -> pathlib.Path:
    """Copies `dm_path`'s contents to a new file sans the `.dm` part.

    The contents of the new file are:

    * A line with the comment:
      "DO NOT EDIT. This file is automatically generated by Duende."
    * The entire (unmodified) contents of `dm_path`.

    {{🌱 The read operation is async}}
    {{🌱 The write operation is async}}
    {{🌱 The output of a call with a normal file starts with the "DO NOT EDIT
         code comment}}
    {{🌱 The output of a call with a normal file contains a copy of the file
         starting at line 2}}
    {{🌱 A call with `dm_path` "foo/bar/quux.dm.py", returns "foo/bar/quux.py"}}

    Returns:
      The path where the copy was made.
    """
    raise NotImplementedError()  # {{🍄 prepare output}}


# If the end user specifies files with globs (e.g., `src/bar/*/age*/fo*.py`),
# the conversational AI should try to search for it and help the user.
dm_path_variable = VariableName('dm_path')

validator_variable = VariableName('validator')

# Value is a block of code that implement a DM marker. See _MarkerImplementation
# for constraints on allowed values.
implementation_variable = VariableName('implementation')

# Value is a comma-separated list of local files that someone implementing a DM
# marker may want to read.
relevant_paths_variable = VariableName('relevant_paths')

MarkerName = NewType('MarkerName', str)


class _MarkerImplementation:

  def __init__(self, name: MarkerName, value: str,
               file_extension: FileExtension) -> None:
    """Sets _name, _value, _file_extension from inputs.

    The value is the full implementation.

    Raises:
      ValueError unless `value` starts and ends with appropriate `✨` comments.
        Per doc/code-specs.md, these comments may contain leading whitespaces.
    """
    raise NotImplementedError()  # {{🍄 marker implementation constructor}}

  # {{🌱 A call to _MarkerImplementation(…).name returns the correct name}}
  # {{🌱 A call to _MarkerImplementation(…).value returns the correct value}}
  # {{🍄 `name` and `value` getters}}

  async def save(self, path: pathlib.Path) -> None:
    """Rewrites `path`, storing our implementation.

    {{🌱 The read operation is async}}
    {{🌱 The write operation is async}}
    {{🌱 Successfully expands a marker in a file with a single marker}}
    {{🌱 Successfully expands the correct marker in a file with ten markers}}
    {{🌱 The value is stored literally, without adding any leading spaces}}
    {{🌱 Raises ValueError if the marker doesn't occur in `path`}}
    {{🌱 Raises ValueError if the marker occurs twice in `path`}}
    {{🌱 Raises FileNotFound if the file does not exist}}
    """
    raise NotImplementedError()  # {{🍄 marker implementation save}}


async def _run_agent_loop(workflow_options: AgentWorkflowOptions,
                          conversation_name: str, start_message_content: str,
                          relevant_files: list[pathlib.Path],
                          done_command: DoneCommand) -> VariableMap:
  """Creates and runs a BaseAgentLoop.

    {{🌱 The command registry given has exactly agent commands:
         ReadFileCommand, ListFilesCommand, SearchFileCommand, done_command}}
    {{🌱 `relevant_files` are read asynchronously}}
    {{🌱 The first content section of the message given to the AgentLoop is
         `start_mesage_content`}}
    {{🌱 There is a content section in the start message given to the AgentLoop
         for each entries in `relevant_files`. It starts with a line
         "File "{path}" follows:" (with the corresponding path) and includes
         the entire contents of the file.}}
    {{🌱 Returns the VariableMap with all the values given to DoneCommand}}

    Args:
      agent_loop_factory: The factory used to create the BaseAgentLoop.
      conversation_name: The name for the conversation that will be created.
      start_message_content: The initial prompt (for start_message).
      files_to_append: A list of files whose contents should be includes in the
        start_message.
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
    input = await self._get_initial_parameters()
    output_path = await input.prepare_output()
    relevant_paths = await self._find_relevant_paths(output_path)
    await self._implement_file(input, output_path, relevant_paths)

    logger.info("CodeSpecsWorkflow completed successfully.")

  async def _get_initial_parameters(self) -> _PathAndValidator:
    """Obtains values to initialize a _PathAndValidator.

    Calls `_run_agent_loop` passing a done_command with `arguments` matching
    `dm_path_variable` and `validator_variable`.
    """

    async def done_validate(inputs: VariableMap) -> ValidationResult:
      """Validates that a _PathAndValidator can be created from `inputs`.

      If _PathAndValidator(…) raises an exception, gives a friendly error
      message to the AI."""
      raise NotImplementedError()  # {{🍄 initial parameters validator}}

    start_message_content = """GOAL: Ask the user (through text conversation) for approprivate values for the variables expected by `done`. Describe these variables to the user to help them understand what is expected (specifically, mention the $DM_PATH environment variable of `validator`).

If the user mentions a file that doesn't exist, try to look for likely typos in their input. Try also to list files in the directory to see if you can guess what the user may have meant.

If the dm_path is a Python file, suggest that the validator could be `mypy` (with an appropriate MYPATH="…" value) or `python3` (with an appropriate PYTHONPATH="…" value).

Once the user has given you appropriate values, your goal is achieved and you should run `done`."""

    raise NotImplementedError  # {{🍄 initial parameters}}

  async def _find_relevant_paths(
      self, path: pathlib.Path) -> dict[MarkerName, set[pathlib.Path]]:
    """Concurrently runs find_relevant_paths_for_marker for all markers."""
    raise NotImplementedError()  # {{🍄 find relevant paths loop}}

  async def _find_relevant_paths_for_marker(
      self, path: pathlib.Path, marker: MarkerName) -> set[pathlib.Path]:
    """Finds all relevant paths to implement a single DM marker.

    Runs an AgentLoop focused exclusively on `marker`, to identify the
    approriate value for relevant_paths_variable.
    """

    async def done_validate(inputs: VariableMap) -> ValidationResult:
      """Verifies that all inputs[relevant_paths_variable] values are readable.

      The files must be readable, and file_access_policy must allow access.
      """
      raise NotImplementedError()  # {{🍄 relevant paths validator}}

    start_message_content = f"""GOAL: identify local file paths that are relevant to replace the line that contains '{{{{{MUSHROOM} {marker}}}}}' from "{path}" (included below) with valid code.

These relevant paths should be given to the `{relevant_paths_variable}` argument of the `done` command.

Example: `done(relevant_paths='src/foo.py,src/bar.cc')`

Feel free to use `read_file`, `list_files` and `search_file` to explore the codebase.
"""

    raise NotImplementedError()  # {{🍄 find relevant paths}}

  async def _implement_file(
      self, inputs: _PathAndValidator, output_path: pathlib.Path,
      relevant_paths: dict[MarkerName, set[pathlib.Path]]) -> None:
    """Implements all DM markers sequentially.

    As it iterates, runs `save` on the return values from `_implement_marker`.
    """
    raise NotImplementedError()  # {{🍄 implement file}}

  async def _implement_marker(
      self, marker: MarkerName, relevant_paths: set[pathlib.Path],
      validator: _Validator,
      output_path: pathlib.Path) -> _MarkerImplementation:
    """Finds a suitable implementation for `marker` from `output_path`.

    Runs an AgentLoop focused exclusively on `marker`. The AI outputs the
    implementation code to `done` through `implementation_variable`. The prompt
    given to the AI is crafted carefully, to explain how it must infer the
    desired intent from `output_path`. All `relevant_paths` are passed to
    _run_agent_loop.

    Arguments:
      marker: The marker to implement.
      relevant_paths: A list of relevant paths. Tells the AI that it must
        read all these paths as well as `output_path` before doing anything else.
      validator: The validator used to verify a plausible implementation.
      output_path: The input file with the context for implementing `marker`. We
        don't actually update it (our customer does).

    Returns:
      A validated _MarkerImplementation that customers can call `save` on.
    """

    async def done_validate(inputs: VariableMap) -> ValidationResult:
      """Validates the implementation (through _MarkerImplementation.save).

      To avoid overwriting `dm_path`, works on a temporary copy.
      """
      raise NotImplementedError()  # {{🍄 implement validator}}

    file_extension = FileExtension(output_path.suffix)
    start_message_content = f"""GOAL: provide the *code content* that will replace the line containing the '{{{{{MUSHROOM} {marker}}}}}' marker in the file '{output_path}'.

The implementation block *must* strictly follow this format:

* It must begin with line containing nothing but "{_comment_string(file_extension, '✨ ' + marker)}" (preceded by whitespace characters to match the indentation of the block that contains the implementation).
* It must end with a line containing nothing but "{_comment_string(file_extension, '✨')}" (also preceded by whitespace).

Once you have the complete and correct implementation code, call the `done` command. The `done` command requires an argument `{implementation_variable}` which *must* be your full implementation block as a single string."""
    raise NotImplementedError()  # {{🍄 implement single marker}}


class CodeSpecsWorkflowFactory(AgentWorkflowFactory):

  def name(self) -> str:
    return "dm"

  async def new(self, agent_workflow_options: AgentWorkflowOptions,
                args: dict[str, str]) -> AgentWorkflow:
    return CodeSpecsWorkflow(agent_workflow_options)
