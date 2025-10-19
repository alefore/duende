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
from typing import Awaitable, Callable, NamedTuple, NewType, Pattern, Sequence

from agent_command import Argument, ArgumentContentType, VariableMap, VariableName, VariableValue
from agent_loop_options import AgentLoopOptions
from agent_loop_options import BaseAgentLoopFactory
from agent_workflow import AgentWorkflow, AgentWorkflowFactory
from agent_workflow_options import AgentWorkflowOptions
from code_specs import FileExtension, MarkerChar, MarkerImplementation, MarkerName, PathAndValidator, Validator, prepare_command_registry, prepare_initial_message, run_agent_loop
from conversation import Conversation, ConversationId, ConversationFactory
from conversation_state import ConversationState
from done_command import DoneCommand, DoneValuesValidator
from list_files_command import ListFilesCommand
from message import Message, ContentSection
from read_file_command import ReadFileCommand
from search_file_command import SearchFileCommand
from validation import ValidationResult
from write_file_command import WriteFileCommand

MUSHROOM = MarkerChar("🍄")

# If the end user specifies files with globs (e.g., `src/bar/*/age*/fo*.py`),
# the conversational AI should try to search for it and help the user.
dm_path_variable = VariableName('dm_path')

validator_variable = VariableName('validator')

# Value is a block of code that implement a DM marker. See MarkerImplementation
# for constraints on allowed values.
implementation_variable = VariableName('implementation')

# Value is a comma-separated list of local files that someone implementing a DM
# marker may want to read.
relevant_paths_variable = VariableName('relevant_paths')


class CodeSpecsWorkflow(AgentWorkflow):

  def __init__(self, options: AgentWorkflowOptions) -> None:
    self._options = options

  async def run(self) -> None:
    input = await self._get_initial_parameters()
    if not input.output_path().exists():
      await input.overwrite(input.output_path())
      relevant_paths = await self._find_relevant_paths(input.output_path())
      await self._implement_file(input, relevant_paths)

  async def _get_initial_parameters(self) -> PathAndValidator:
    """Obtains values to initialize a PathAndValidator.

    Calls `run_agent_loop` passing outputs of `prepare_command_registry` and
    `prepare_initial_message`.
    """

    async def done_validator(inputs: VariableMap) -> ValidationResult:
      """Validates that a PathAndValidator can be created from `inputs`.

      If PathAndValidator(…) raises an exception, gives a friendly error
      message to the AI."""
      raise NotImplementedError()  # {{🍄 initial parameters validator}}

    start_message_content = (
        "GOAL: Ask the user (through text conversation) for approprivate values "
        "for the variables expected by `done`. "
        "Describe these variables to the user "
        "to help them understand what is expected "
        "(mention the $DM_PATH environment variable of `validator`)."
        "\n"
        "If the user mentions a file that doesn't exist, "
        "try to look for likely typos in their input. "
        "Try also to list files in the directory "
        "to see if you can guess what the user may have meant."
        "\n"
        "If the dm_path is a Python file, "
        "suggest that the validator could be `mypy` "
        "(with an appropriate MYPATH=\"…\" value) "
        "or `python3` (with an appropriate PYTHONPATH=\"…\" value)."
        "\n"
        "Once the user has given you appropriate values, "
        "your goal is achieved and you should run `done`.")
    raise NotImplementedError  # {{🍄 initial parameters}}

  async def _find_relevant_paths(
      self, path: pathlib.Path) -> dict[MarkerName, set[pathlib.Path]]:
    """Finds all relevant markers.

    {{🦔 Calls `find_relevant_paths_for_marker` exactly once for each marker
         found in `path`.}}
    {{🦔 Calls to `find_relevant_paths_for_marker` happen concurrently.}}
    {{🦔 The output contains one entry for each marker found in `path`.}}
    {{🦔 The output values correspond to the outputs of
         `_find_relevant_paths_for_marker` for each key (marker).}}
    """
    raise NotImplementedError()  # {{🍄 find relevant paths loop}}

  async def _find_relevant_paths_for_marker(
      self, path: pathlib.Path, marker: MarkerName) -> set[pathlib.Path]:
    """Finds all relevant paths to implement a single DM marker.

    Calls `run_agent_loop` passing outputs of `prepare_command_registry` and
    `prepare_initial_message`. The agent is focused exclusively on `marker`,
    with the goal of identifying the best value for `relevant_paths_variable`.
    """

    async def done_validate(inputs: VariableMap) -> ValidationResult:
      """Verifies that all inputs[relevant_paths_variable] values are readable.

      {{🦔 If no files are given, validation fails, with a message that at least
           one relevant file should be given.}}
      {{🦔 All files must be readable (both by the OS as well as allowed by the
           `file_access_policy`). If one isn't, validation fails.}}
      {{🦔 If all files are readable (both by the OS and `file_access_policy`),
           validation succeeds.}}
      """
      raise NotImplementedError()  # {{🍄 relevant paths validator}}

    start_message_content = (
        f"GOAL: identify local file paths that are relevant "
        f"to replace the line that contains '{{{{{MUSHROOM} {marker}}}}}' "
        f"from \"{path}\" (included below) with valid code."
        f"\n"
        f"These relevant paths should be given to the "
        f"`{relevant_paths_variable}` argument of the `done` command."
        f"\n"
        f"Example: `done(relevant_paths=\"src/foo.py,src/bar.cc\")"
        f"\n"
        f"Feel free to use `read_file`, `list_files` and `search_file` "
        f"to explore the codebase.")

    raise NotImplementedError()  # {{🍄 find relevant paths}}

  async def _implement_file(
      self, inputs: PathAndValidator,
      relevant_paths: dict[MarkerName, set[pathlib.Path]]) -> None:
    """Implements all DM markers in `inputs.output_path()` sequentially.

    {{🦔 The calls to `_implement_marker` happen sequentially.}}
    {{🦔 The output of a call to `_implement_marker` is stored through
         `MarkerImplementation.save` on `inputs.output_path()`.}}
    {{🦔 The output of a call to `_implement_marker` is stored before the next
         call begins (so that the next call already sees the output of the
         previous call).}}
    """
    raise NotImplementedError()  # {{🍄 implement file}}

  async def _implement_marker(
      self, marker: MarkerName, relevant_paths: set[pathlib.Path],
      validator: Validator, output_path: pathlib.Path) -> MarkerImplementation:
    """Finds a suitable implementation for `marker` from `output_path`.

    Calls `run_agent_loop` passing outputs of `prepare_command_registry` and
    `prepare_initial_message`. The agent is focused exclusively on `marker`,

    The AI outputs the implementation code to `done` through
    `implementation_variable`.

    {{🦔 For each file in `relevant_paths`, there's a section in the initial
         message given to the AI.}}

    Arguments:
      marker: The marker to implement.
      relevant_paths: A list of relevant paths. Tells the AI that it must
        read all these paths as well as `output_path` before doing anything else.
      validator: The validator used to verify a plausible implementation.
      output_path: The input file with the context for implementing `marker`. We
        do not actually update it (our customer does).

    Returns:
      A validated MarkerImplementation that customers can call `save` on.
    """

    async def done_validate(inputs: VariableMap) -> ValidationResult:
      """Calls validator.validate_marker_implementation to validate."""
      raise NotImplementedError()  # {{🍄 implement validator}}

    file_extension = FileExtension(output_path.suffix)
    start_message_content = (
        "GOAL: provide the *code content* "
        "that will replace the line containing the "
        f"'{{{{{MUSHROOM} {marker}}}}}' marker in the file '{output_path}'."
        "\n"
        "The implementation block *must* strictly follow this format:"
        "\n"
        "* It must begin with line containing nothing but "
        "\"{_comment_string(file_extension, '✨ ' + marker)}\" "
        "(preceded by whitespace characters to match "
        "the indentation of the block that contains the implementation)."
        "\n"
        "It must end with a line containing "
        "nothing but \"{_comment_string(file_extension, '✨')}\" "
        "(also preceded by whitespace)."
        "\n"
        "Once you have the complete and correct implementation code, "
        "call the `done` command. "
        "The `done` command requires an argument `{implementation_variable}` "
        "which *must* be your full implementation block as a single string.")
    raise NotImplementedError()  # {{🍄 implement single marker}}


class CodeSpecsWorkflowFactory(AgentWorkflowFactory):

  def name(self) -> str:
    return "dm"

  async def new(self, agent_workflow_options: AgentWorkflowOptions,
                args: dict[str, str]) -> AgentWorkflow:
    return CodeSpecsWorkflow(agent_workflow_options)
