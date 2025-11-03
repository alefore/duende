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
from code_specs import FileExtension, MarkerChar, MarkerImplementation, MarkerName, PathAndValidator, Validator, comment_string, get_markers, prepare_command_registry, prepare_initial_message, relevant_paths_variable, run_agent_loop
from conversation import Conversation, ConversationId, ConversationFactory
from conversation_state import ConversationState
from done_command import DoneCommand, DoneValuesValidator
from list_files_command import ListFilesCommand
from message import Message, ContentSection
import output_cache
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


class CodeSpecsWorkflow(AgentWorkflow):

  def __init__(self, options: AgentWorkflowOptions) -> None:
    self._options = options
    self._output_cache = output_cache.OutputCache(output_cache.DEFAULT_PATH)

  async def run(self) -> None:
    input = await self._get_initial_parameters()
    await self._prepare_output_path(input)
    relevant_paths = await self._find_relevant_paths(input.output_path())
    await self._implement_file(input, relevant_paths)

  async def _get_initial_parameters(self) -> PathAndValidator:
    """Obtains values to initialize a PathAndValidator.

    Calls `run_agent_loop` passing outputs of `prepare_command_registry` and
    `prepare_initial_message`.

    {{🦔 The done command arguments given to `prepare_command_registry` are
         `dm_path_variable` and `validator_variable`.}}
    {{🦔 Does *not* enable caching of conversations (through output_cache).}}
    """

    async def done_validator(inputs: VariableMap) -> ValidationResult:
      """Validates that a PathAndValidator can be created from `inputs`.

      On any failure, gives a very friendly and helpful explanation message to
      the AI.

      {{🦔 If the dm_path has repeated (identical) MUSHROOM markers (per
           `code_specs.get_markers`), validation fails with an explanation.}}
      {{🦔 Catches exceptions from PathAndValidator and turns them into a
           failed `ValidationResult`.}}
      """
      raise NotImplementedError()  # {{🍄 initial parameters validator}}

    start_message_content = (
        "GOAL: Ask the user (through text conversation) for approprivate values "
        "for the variables expected by `done`. "
        "Describe these variables to the user "
        "to help them understand what is expected "
        "(mention the $DMPATH environment variable of `validator`)."
        "\n"
        "If the user mentions a file that doesn't exist, "
        "try to look for likely typos in their input. "
        "Try also to list files in the directory "
        "to see if you can guess what the user may have meant. "
        "Your goal is to figure out which file the user means "
        "even if the user is sloppy or lazy "
        "(maybe he is too busy; "
        "or is typing on a phone with broken autocomplete). "
        "Try to save the user time."
        "\n"
        "Once the user has mentioned a file, "
        "read it and try to see if the file suggests "
        "what to use as the validator for its own expansion, "
        "typically near the top of the file."
        "\n"
        "If the dm_path is a Python file, "
        "suggest that the validator could be `mypy` "
        "(with an appropriate MYPATH=\"…\" value) "
        "or `python3` (with an appropriate PYTHONPATH=\"…\" value)."
        "\n"
        "Once the user has given you appropriate values "
        "(or you have inferred them), "
        "your goal is achieved and you should run `done`.")
    raise NotImplementedError  # {{🍄 initial parameters}}

  async def _prepare_output_path(
      self, input: PathAndValidator) -> pathlib.Path | None:
    """Prepares various files, moving old implementations aside."""
    return_value: pathlib.Path | None = None
    if input.output_path().exists():
      # {{🦔 `input.output_path()` is copied to `input.output_path().old`
      #      (for example, `src/foo.py` becomes `src/foo.py.old`).}}
      # {{🦔 `return_value` is set to the location of the copy (`….old`).}}
      raise NotImplementedError  # {{🍄 prepare output paths if old output}}

    # {{🦔 Unconditionally overwrites `input.output_path()` with
    #   `input.dm_path` (after moving it to a temporary file).}}
    raise NotImplementedError  # {{🍄 prepare output path}}

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

    {{🦔 The only done command argument given to `prepare_command_registry` is
         `relevant_paths_variable`.}}
    {{🦔 Enables caching of conversations: if two separate instances of
         CodeSpecsWorkflow have this method called with the same inputs,
         the 2nd call reuses the outputs from the first.}}
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
        f"to replace the line that contains '{{{{{MUSHROOM} {marker.name}}}}}' "
        f"from \"{path}\" (included below) with valid code."
        f"\n"
        f"These relevant paths should be given to the "
        f"`{relevant_paths_variable}` argument of the `done` command."
        f"\n"
        f"Example: `done(relevant_paths=\"src/foo.py,src/bar.cc\")"
        f"\n"
        f"Feel free to use `read_file`, `list_files` and `search_file` "
        f"to explore the codebase.")

    # Enable caching in the options given to `run_agent_loop`:
    options = self._options._replace(
        agent_loop_factory=output_cache.CachingDelegatingAgentLoopFactory(
            f"code_specs_workflow:{path}", self._output_cache,
            self._options.agent_loop_factory))
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
    {{🦔 The calls to `_implement_marker` happen in the order in which the
         markers occur in the DM file.}}
    """
    raise NotImplementedError()  # {{🍄 implement file}}

  async def _implement_marker(
      self,
      inputs: PathAndValidator,
      marker: MarkerName,
      relevant_paths: set[pathlib.Path],
  ) -> MarkerImplementation:
    """Finds a suitable implementation for `marker` from `inputs`.

    Calls `run_agent_loop` passing outputs of `prepare_command_registry` and
    `prepare_initial_message`. The agent is focused exclusively on `marker`,

    The AI outputs the implementation code to `done` through
    `implementation_variable`.

    {{🦔 For each file in `relevant_paths`, there's a section in the initial
         message (prompt) given to the AI.}}
    {{🦔 If `inputs.old_path()` exists and contains an implementation for
         `marker`, that implementation gets included as the last section of the
         initial message. The section is the line "Previous implementation:",
         followed by the entire implementation (of the marker).}}
    {{🦔 The only done command argument given to `prepare_command_registry` is
         `implementation_variable`.}}
    {{🦔 Enables caching of conversations: if two separate instances of
         CodeSpecsWorkflow have this method called for the same inputs.dm_path
         and marker, the 2nd call reuses the outputs from the first.}}
    {{🦔 Doesn't actually overwrite any files (the caller does).}}

    Arguments:
      marker: The marker to implement.
      inputs: The dm file we're inspecting.
      relevant_paths: A list of relevant paths for the initial prompt.

    Returns:
      A validated MarkerImplementation that customers can call `save` on.
    """

    async def done_validate(inputs: VariableMap) -> ValidationResult:
      """Calls validator.validate_marker_implementation to validate."""
      raise NotImplementedError()  # {{🍄 implement validator}}

    file_extension = FileExtension(inputs.output_path().suffix[1:])
    start_message_content = (
        "GOAL: provide the *code content* "
        "that will replace the line containing the "
        f"'{{{{{MUSHROOM} {marker.name}}}}}' marker "
        f"in the file '{inputs.output_path()}'."
        "\n"
        "The implementation block *must* strictly follow this format:"
        "\n"
        "* It must begin with line containing nothing but "
        f"\"{comment_string(file_extension, '✨ ' + marker.name)}\" "
        "(preceded by whitespace characters to match "
        "the indentation of the block that contains the implementation)."
        "\n"
        "* It must end with a line containing "
        f"nothing but \"{comment_string(file_extension, '✨')}\" "
        "(also preceded by whitespace)."
        "\n"
        "Once you have the complete and correct implementation code, "
        "call the `done` command. "
        f"The `done` command requires an argument `{implementation_variable}` "
        "which *must* be your full implementation block as a single string.")

    # Content to append *conditionally* if `inputs.old_path()` exists:
    additional_start_message_content_if_old_implementation_available = (
        f"In your implementation, try to reuse as much as possible the old "
        f"implementation (included in the initial message). "
        f"Only change the implementation if this is strictly necessary: "
        f"if the old implementation has bugs "
        f"(e.g., does not honor some documented property), "
        f"new requirements have been added, "
        f"or requirements have been removed/relaxed "
        f"(in ways that allow code simplifications).")

    # Enable caching in the options given to `run_agent_loop`:
    options = self._options._replace(
        agent_loop_factory=output_cache.CachingDelegatingAgentLoopFactory(
            f"code_specs_workflow:{inputs.output_path()}", self._output_cache,
            self._options.agent_loop_factory))

    raise NotImplementedError()  # {{🍄 implement single marker}}


class CodeSpecsWorkflowFactory(AgentWorkflowFactory):

  def name(self) -> str:
    return "dm"

  async def new(self, agent_workflow_options: AgentWorkflowOptions,
                args: dict[str, str]) -> AgentWorkflow:
    return CodeSpecsWorkflow(agent_workflow_options)
