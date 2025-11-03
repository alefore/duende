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
from ask_command import AskCommand
from code_specs import FileExtension, MarkerChar, MarkerName, MarkersOverlapError, comment_string, get_markers, relevant_paths_variable
from code_specs_agent import prepare_command_registry, prepare_initial_message, run_agent_loop
from code_specs_commands import ListDuendeMarkerImplementationCommand, UpdateDuendeMarkerImplementationCommand, ReadDuendeImplementationMarkerCommand
from code_specs_marker_implementation import MarkerImplementation
from code_specs_path_and_validator import PathAndValidator
from code_specs_validator import Validator
from conversation import Conversation, ConversationId, ConversationFactory
from conversation_state import ConversationState
from done_command import DoneCommand, DoneValuesValidator
from list_files_command import ListFilesCommand
from message import Message, ContentSection
from read_file_command import ReadFileCommand
from search_file_command import SearchFileCommand
from validation import ValidationResult
from write_file_command import WriteFileCommand

# A token like "{{" + HEDGEHOG + " " + description + "}}" defines a property for
# which a unit test should be written (validating that the property holds).
HEDGEHOG = MarkerChar("🦔")

MUSHROOM = MarkerChar("🍄")

# The full name to a test, including the file in which it is defined (and likely
# the class, if the test is a method in a class). This is returned by `pytest`
# and can be given directly to `pytest` (without the need to add any prefixes).
TestName = NewType("TestName", str)

# Path to a file with unittests.
tests_path_variable = VariableName('tests_path')

PYTEST_BINARY = os.getenv("PYTEST") or "pytest"


class CodeSpecsTestsEnableWorkflow(AgentWorkflow):
  """Starts executing tests gradually, fixing them (or code) until all pass."""

  def __init__(self, options: AgentWorkflowOptions) -> None:
    self._options = options

  async def run(self) -> None:
    input = await self._get_initial_parameters()
    tests = await self._list_tests(input)
    for i in range(len(tests)):
      await self._make_tests_pass(input, tests[0:i + 1])

  async def _list_tests(self, input: pathlib.Path) -> list[TestName]:
    """Uses `pytest` to list all tests in `input`.

    {{🦔 Returns an empty list on an empty file.}}
    {{🦔 Returns an empty list on a non-empty file that contains valid python
         code but no tests.}}
    """
    raise NotImplementedError()  # {{🍄 list tests}}

  async def _get_initial_parameters(self) -> pathlib.Path:
    """Obtains the path with tests to enable.

    Calls `run_agent_loop` passing outputs of `prepare_command_registry` and
    `prepare_initial_message`.

    {{🦔 The only done command argument given to `prepare_command_registry` is
         `tests_path_variable`.}}
    """

    async def done_validator(inputs: VariableMap) -> ValidationResult:
      """Validates that tests_path_variable points to a correct path.

      {{🦔 Validation fails if the file can't be read.}}
      {{🦔 Validation fails if the file does not contain any tests (per
           `_list_tests`).}}
      {{🦔 Validation succeeds if the file can be read.}}
      {{🦔 Does not require any variables other than `tests_path_variable`.}}
      """
      raise NotImplementedError()  # {{🍄 initial parameters validator}}

    start_message_content = (
        "GOAL: Ask the user (through text conversation) "
        "for approprivate values "
        "for the variables expected by `done`. "
        "Describe these variables to the user "
        "to help them understand what is expected."
        "\n"
        "If the user mentions a file that doesn't exist, "
        "try to look for likely typos in their input. "
        "Try also to list files in the directory "
        "to see if you can guess what the user may have meant."
        "\n"
        "Once the user has given you appropriate values, "
        "your goal is achieved and you should run `done`.")
    raise NotImplementedError  # {{🍄 initial parameters}}

  async def _run_tests(self, tests: list[TestName]) -> str | None:
    """Runs the tests given and returns an optional string with failure info.

    {{🦔 If all tests listed in `tests` pass, returns None.}}
    {{🦔 If at least one test (from `tests`) fails, returns a string with a
         description of the failures.}}
    {{🦔 Only runs the tests listed in `tests`; additional tests in `input` do
         not run.}}
    """
    raise NotImplementedError  # {{🍄 run tests}}

  async def _make_tests_pass(self, input: pathlib.Path,
                             tests: list[TestName]) -> None:
    """Runs an agent to fix any failing  tests (from `tests`).

    Calls `run_agent_loop`.

    {{🦔 If all tests already pass (when this is called), no agent is created.}}
    {{🦔 If at least one test is failing (when this is called), runs an agent.}}
    {{🦔 If an agent is run, it is given an initial prompt that includes the
         failure information (output of `_run_tests`).}}
    {{🦔 If an agent is run, it receives `input` in `relevant_files`.}}
    {{🦔 No `done` command argument is given to `prepare_command_registry`.}}
    {{🦔 The command registry given to the agent includes `WriteFileCommand`.}}
    {{🦔 The command registry given to the agent includes
         `ListDuendeMarkerImplementationCommand`.}}
    {{🦔 The command registry given to the agent includes:
         * `ListDuendeMarkerImplementationCommand`
         * `UpdateDuendeMarkerImplementationCommand`
         * `ReadDuendeImplementationMarkerCommand`
         * `AskCommand`}}
    {{🦔 The name of the conversation includes `len(tests)` followed by the last
         value in `tests`.}}
    """

    async def done_validator(inputs: VariableMap) -> ValidationResult:
      """Validates that all tests in `tests` pass.

      {{🦔 Validation fails if at least one test (from `tests`) doesn't pass.}}
      {{🦔 Validation succeeds if all tests (from `tests`) pass.}}
      {{🦔 Validation doesn't depend on `inputs`.}}
      {{🦔 If validation fails, all information about the failures is given in
           the output (to help the AI understand what's missing).}}
      """
      raise NotImplementedError()  # {{🍄 make tests pass validator}}

    start_message_content = (
        "GOAL: Make unit tests pass. "
        "To do this, first determine "
        "whether the problem is in the failing tests "
        "or in the implementation. "
        "Give an explanation in English to support your conclusion. "
        "Then adjust the root cause of the problem and call `done`.\n"
        "As much as possible, "
        "prefer using `update_duende_marker_implementation` "
        "in order to update blocks "
        "(rather than writing entire files).\n"
        "Calling `done` will cause the tests in scope to be executed "
        "and will confirm that you've successfully fixed the problem.\n"
        "We may not be executing all tests but only a subset. That's OK. "
        "You should focus only on fixing the explicit failures.\n"
        "Avoid loading too much information: "
        "prefer using `ask` to fork other conversations "
        "that figure out the answer to specific questions.")
    raise NotImplementedError()  # {{🍄 make tests pass}}


class CodeSpecsTestsEnableWorkflowFactory(AgentWorkflowFactory):

  def name(self) -> str:
    return "dm-tests-enable"

  async def new(self, agent_workflow_options: AgentWorkflowOptions,
                args: dict[str, str]) -> AgentWorkflow:
    return CodeSpecsTestsEnableWorkflow(agent_workflow_options)
