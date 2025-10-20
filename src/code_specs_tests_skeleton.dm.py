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
from code_specs import FileExtension, MarkerChar, MarkerImplementation, MarkerName, PathAndValidator, Validator, comment_string, get_markers, prepare_command_registry, prepare_initial_message, run_agent_loop
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

TestName = NewType("TestName", str)


@dataclasses.dataclass(frozen=True)
class TestMetadata:
  # The `description` string in the HEDGEHOG marker.
  property: str
  # A valid name for the test.
  name: TestName


@dataclasses.dataclass(frozen=True)
class TestImplementation:
  metadata: TestMetadata
  code: str


# Path to a file that contains `HEDGEHOG` markers describing properties that we
# want to test.
path_to_test_variable = VariableName('path_to_tests')

tests_skeleton_variable = VariableName('tests_skeleton')


class CodeSpecsTestsSkeletonWorkflow(AgentWorkflow):
  """Turns a DM file with HEDGEHOG markers into a DM file for the tests."""

  def __init__(self, options: AgentWorkflowOptions) -> None:
    self._options = options

  async def run(self) -> None:
    input = await self._get_initial_parameters()
    await self._prepare_tests_skeleton(input)

  async def _get_initial_parameters(self) -> pathlib.Path:
    """Obtains the path to test.

    Calls `run_agent_loop` passing outputs of `prepare_command_registry` and
    `prepare_initial_message`.

    {{🦔 The only done command argument given to `prepare_command_registry` is
         `path_to_test_variable`.}}
    """

    async def done_validator(inputs: VariableMap) -> ValidationResult:
      """Validates that path_to_test points to a correct path.

      {{🦔 Validation fails if the file can't be read.}}
      {{🦔 Validation fails if the file doesn't contain any HEDGEHOG markers
           (per `code_specs.get_markers`).}}
      {{🦔 Validation succeeds if the file can be read and contains HEDGEHOG
           markers (per `code_specs.get_markers`).}}
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

  async def _prepare_tests_skeleton(self, input: pathlib.Path) -> None:
    """Runs an AgentLoop to create a skeleton for the tests.

    {{🦔 The only done command argument given to `prepare_command_registry` is
         `path_to_test_variable`.}}
    {{🦔 After validating that the skeleton contains all tests, writes them to
         a `tests_…` file (e.g., for `src/foo.py`, writes `src/test_foo.py`).}}
    """
    start_message_content = (
        f"GOAL: Prepare a skeleton file for unit tests "
        f"based on the contents of file \"{input}\". "
        f"This file contains markers that look like this: "
        f"\"{{{HEDGEHOG} property to validate}}\" "
        f"(where \"property to validate\" is a description "
        f"of what the test should do). "
        f"Your skeleton should contain a unit test "
        f"for each of these markers, something like this:"
        f"\n\n"
        f"    await def test_foo_bar_name_here(self) -> None:\n"
        f"      pass  # {{{MUSHROOM} property to validate}}\n"
        f"\n"
        f"(The `await` keyword may not be necessary, "
        f"in which case it should be omitted; "
        f"the tests should be in a subclass either of `unittest.TestCase` "
        f"or `unittest.IsolatedAsyncioTestCase`)."
        f"\n"
        f"The input file may contain repeated {{{HEDGEHOG} …}} markers; "
        f"for example, multiple functions may share an identical property. "
        f"However, {{{MUSHROOM} …}} markers must be identical in the output. "
        f"That means that if you find repeated {HEDGEHOG} markers, "
        f"you must add more information inside the output markers "
        f"in order to disambiguate them."
        f"\n"
        f"Please try to pick meaningful names for the tests "
        f"(as in the example `test_foo_bar_name_here`) based on both "
        f"(1) the text inside the curly braces (after the \"{HEDGEHOG}\", "
        f"and (2) the context around the line where the token occurs "
        f"(for example, if the token is given in a function's docstring, "
        f"it's very likely that it refers to tests for that function)."
        f"\n"
        f"As you can see, you are not actually going to implement the tests, "
        f"but you're just laying down the foundation. "
        f"We are turning the {{{HEDGEHOG} …}} markers "
        f"into {{{MUSHROOM} …}} markers, "
        f"which will drive the implementation of the tests."
        f"\n"
        f"Make sure to include this at the end of the file:"
        f"\n"
        f"\n"
        f"    if __name__ == '__main__':\n"
        f"      unittest.main()\n"
        f"\n"
        f"Once you're done, run `done`, "
        f"passing the entirety of the skeleton "
        f"as parameter {tests_skeleton_variable}.")

    async def done_validate(inputs: VariableMap) -> ValidationResult:
      """Validates that tests_skeleton_variable has the right markers.

      Fails if the set of markers given in tests_skeleton_variable (per
      `code_spec.get_markers(MUSHROOM, output)` isn't valid
      (for example, it contains repeated markers).

      Also fails if the number of HEDGEHOG markers in the input
      isn't exactly the same as the number of MUSHROOM markers in the output.
      """
      raise NotImplementedError()  # {{🍄 tests skeleton validator}}

    raise NotImplementedError()  # {{🍄 prepare tests skeleton}}


class CodeSpecsTestsSkeletonWorkflowFactory(AgentWorkflowFactory):

  def name(self) -> str:
    return "dm-tests"

  async def new(self, agent_workflow_options: AgentWorkflowOptions,
                args: dict[str, str]) -> AgentWorkflow:
    return CodeSpecsTestsSkeletonWorkflow(agent_workflow_options)
