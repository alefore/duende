# DM validator:
#
# mypy $DMPATH && $PYTHON -m pytest $DMPATH
#
# See src/test-constraints.md for constraints that apply to these tests.

import aiofiles
import asyncio
import pathlib
import tempfile
import unittest
from typing import Awaitable, Callable
from unittest import mock

from agent_command import Argument, ArgumentContentType, CommandInput, CommandOutput, VariableMap, VariableName, VariableValueStr
from agent_loop import AgentLoopFactory
from agent_loop_options import AgentLoopOptions, BaseAgentLoopFactory
from agent_workflow_options import AgentWorkflowOptions
from code_specs import FileExtension, MarkerName, comment_string, relevant_paths_variable
from code_specs_agent import prepare_command_registry, prepare_initial_message, run_agent_loop
from code_specs_path_and_validator import PathAndValidator
from code_specs_validator import Validator
from code_specs_workflow import CodeSpecsWorkflow, dm_path_variable, validator_variable, implementation_variable
from command_registry import CommandRegistry
from conversation import ConversationFactory, ConversationFactoryOptions, Conversation
from conversation_state import ConversationState
from conversational_ai_test_utils import FakeConversationalAIConversation, FakeConversationalAI
from done_command import DoneCommand, DoneValuesValidator
from file_access_policy import FileAccessPolicy
from list_files_command import ListFilesCommand
from message import ContentSection, Message
from read_file_command import ReadFileCommand
from search_file_command import SearchFileCommand
from selection_manager import SelectionManager
from test_utils import FakeFileAccessPolicy, FakeConfirmationState, FakeConfirmationManager, FakeSelectionManager, slow_conversation_factory_options
from validation import ValidationResult


def _message_done_path_validator(dm_path: pathlib.Path,
                                 validator: str) -> Message:
  """Returns a role=assistant Message calling `done`.

  Passes values for dm_path_variable and validator_variable.
  """
  raise NotImplementedError()  # {{🍄 message done path validator}}


def _message_done_relevant_paths(paths: list[pathlib.Path]) -> Message:
  """Returns a role=assistant Message calling `done`.

  Passes values for relevant_paths_variable."""
  raise NotImplementedError()  # {{🍄 message done relevant paths}}


def _content_with_markers(markers: list[str]) -> str:
  """Returns a string with a Python file containing the 🍄 markers given."""
  raise NotImplementedError()  # {{🍄 content with markers}}


class TestCodeSpecsWorkflow(unittest.IsolatedAsyncioTestCase):

  def setUp(self) -> None:
    self.conversation_factory: ConversationFactory = ConversationFactory(
        slow_conversation_factory_options())

  def _find_conversation(self, conversation_name) -> Conversation:
    """Finds and returns a conversation (uses self.fail + assert)."""
    raise NotImplementedError()  # {{🍄 find conversation by name}}

  async def build_workflow(
      self, scripted_messages: dict[str, list[Message]]) -> CodeSpecsWorkflow:
    """Sets up a CodeSpecWorkflow with fake objects.

    Sets option skip_implicit_validation to True.
    """
    raise NotImplementedError()  # {{🍄 build workflow}}

  def filter_content_sections(
      self, predicate: Callable[[ContentSection],
                                bool]) -> list[ContentSection]:
    """Returns any content sections in any messages that match a predicate.

    Extracts the messages from self.conversation_factory."""
    raise NotImplementedError()  # {{🍄 filter content sections}}

  async def test_codespecsworkflow__get_initial_parameters_the_done_command_arguments_given_to_prepare_command_registry_are_dm_path_variable_and_validator_variable_1(
      self) -> None:
    pass  # {{🍄 The done command arguments given to `prepare_command_registry` are `dm_path_variable` and `validator_variable`. (in CodeSpecsWorkflow._get_initial_parameters)}}

  async def test_codespecsworkflow__get_initial_parameters_does_not_enable_caching_of_conversations_through_output_cache_1(
      self) -> None:
    pass  # {{🍄 Does *not* enable caching of conversations (through output_cache). (in CodeSpecsWorkflow._get_initial_parameters)}}

  async def test_codespecsworkflow__get_initial_parameters_done_validator_if_the_dm_path_has_repeated_identical_mushroom_markers_per_code_specsget_markers_validation_fails_with_an_explanation_1(
      self) -> None:
    pass  # {{🍄 If the dm_path has repeated (identical) MUSHROOM markers (per `code_specs.get_markers`), validation fails with an explanation. (in CodeSpecsWorkflow._get_initial_parameters.done_validator)}}

  async def test_codespecsworkflow__get_initial_parameters_done_validator_catches_exceptions_from_pathandvalidator_and_turns_them_into_a_failed_validationresult_1(
      self) -> None:
    pass  # {{🍄 Catches exceptions from PathAndValidator and turns them into a failed `ValidationResult`. (in CodeSpecsWorkflow._get_initial_parameters.done_validator)}}

  async def test_codespecsworkflow__prepare_output_path_if_it_exists_inputoutput_path_is_copied_to_inputold_path_1(
      self) -> None:
    pass  # {{🍄 If it exists, `input.output_path()` is copied to `input.old_path()`. (in CodeSpecsWorkflow._prepare_output_path)}}

  async def test_codespecsworkflow__prepare_output_path_unconditionally_overwrites_inputoutput_path_with_inputdm_path_after_copying_it_to_old_path_1(
      self) -> None:
    pass  # {{🍄 Unconditionally overwrites `input.output_path()` with `input.dm_path` (after copying it to `old_path`). (in CodeSpecsWorkflow._prepare_output_path)}}

  async def test_codespecsworkflow__find_relevant_paths_calls_find_relevant_paths_for_marker_exactly_once_for_each_marker_found_in_path_1(
      self) -> None:
    pass  # {{🍄 Calls `find_relevant_paths_for_marker` exactly once for each marker found in `path`. (in CodeSpecsWorkflow._find_relevant_paths)}}

  async def test_codespecsworkflow__find_relevant_paths_calls_to_find_relevant_paths_for_marker_happen_concurrently_1(
      self) -> None:
    pass  # {{🍄 Calls to `find_relevant_paths_for_marker` happen concurrently. (in CodeSpecsWorkflow._find_relevant_paths)}}

  async def test_codespecsworkflow__find_relevant_paths_the_output_contains_one_entry_for_each_marker_found_in_path_1(
      self) -> None:
    pass  # {{🍄 The output contains one entry for each marker found in `path`. (in CodeSpecsWorkflow._find_relevant_paths)}}

  async def test_codespecsworkflow__find_relevant_paths_the_output_values_correspond_to_the_outputs_of__find_relevant_paths_for_marker_for_each_key_marker_1(
      self) -> None:
    pass  # {{🍄 The output values correspond to the outputs of `_find_relevant_paths_for_marker` for each key (marker). (in CodeSpecsWorkflow._find_relevant_paths)}}

  async def test_codespecsworkflow__find_relevant_paths_for_marker_the_only_done_command_argument_given_to_prepare_command_registry_is_relevant_paths_variable_1(
      self) -> None:
    pass  # {{🍄 The only done command argument given to `prepare_command_registry` is `relevant_paths_variable`. (in CodeSpecsWorkflow._find_relevant_paths_for_marker)}}

  async def test_codespecsworkflow__find_relevant_paths_for_marker_enables_caching_of_conversations_if_two_separate_instances_of_codespecsworkflow_have_this_method_called_with_the_same_inputs_the_2nd_call_reuses_the_outputs_from_the_first_1(
      self) -> None:
    pass  # {{🍄 Enables caching of conversations: if two separate instances of CodeSpecsWorkflow have this method called with the same inputs, the 2nd call reuses the outputs from the first. (in CodeSpecsWorkflow._find_relevant_paths_for_marker)}}

  async def test_codespecsworkflow__find_relevant_paths_for_marker_done_validate_if_no_files_are_given_validation_fails_with_a_message_that_at_least_one_relevant_file_should_be_given_1(
      self) -> None:
    pass  # {{🍄 If no files are given, validation fails, with a message that at least one relevant file should be given. (in CodeSpecsWorkflow._find_relevant_paths_for_marker.done_validate)}}

  async def test_codespecsworkflow__find_relevant_paths_for_marker_done_validate_all_files_must_be_readable_both_by_the_os_as_well_as_allowed_by_the_file_access_policy_if_one_isnt_validation_fails_1(
      self) -> None:
    pass  # {{🍄 All files must be readable (both by the OS as well as allowed by the `file_access_policy`). If one isn't, validation fails. (in CodeSpecsWorkflow._find_relevant_paths_for_marker.done_validate)}}

  async def test_codespecsworkflow__find_relevant_paths_for_marker_done_validate_if_all_files_are_readable_both_by_the_os_and_file_access_policy_validation_succeeds_1(
      self) -> None:
    pass  # {{🍄 If all files are readable (both by the OS and `file_access_policy`), validation succeeds. (in CodeSpecsWorkflow._find_relevant_paths_for_marker.done_validate)}}

  async def test_codespecsworkflow__implement_file_the_calls_to__implement_marker_happen_sequentially_1(
      self) -> None:
    pass  # {{🍄 The calls to `_implement_marker` happen sequentially. (in CodeSpecsWorkflow._implement_file)}}

  async def test_codespecsworkflow__implement_file_the_output_of_a_call_to__implement_marker_is_stored_through_markerimplementation_save_on_inputsoutput_path_1(
      self) -> None:
    pass  # {{🍄 The output of a call to `_implement_marker` is stored through `MarkerImplementation.save` on `inputs.output_path()`. (in CodeSpecsWorkflow._implement_file)}}

  async def test_codespecsworkflow__implement_file_the_output_of_a_call_to__implement_marker_is_stored_before_the_next_call_begins_so_that_the_next_call_already_sees_the_output_of_the_previous_call_1(
      self) -> None:
    pass  # {{🍄 The output of a call to `_implement_marker` is stored before the next call begins (so that the next call already sees the output of the previous call). (in CodeSpecsWorkflow._implement_file)}}

  async def test_codespecsworkflow__implement_file_the_calls_to__implement_marker_happen_in_the_order_in_which_the_markers_occur_in_the_dm_file_1(
      self) -> None:
    pass  # {{🍄 The calls to `_implement_marker` happen in the order in which the markers occur in the DM file. (in CodeSpecsWorkflow._implement_file)}}

  async def test_codespecsworkflow__implement_marker_for_each_file_in_relevant_paths_theres_a_section_in_the_initial_message_prompt_given_to_the_ai_1(
      self) -> None:
    pass  # {{🍄 For each file in `relevant_paths`, there's a section in the initial message (prompt) given to the AI. (in CodeSpecsWorkflow._implement_marker)}}

  async def test_codespecsworkflow__implement_marker_if_path_and_validatorold_path_exists_and_contains_an_implementation_for_marker_that_implementation_gets_included_as_the_last_section_of_the_initial_message_the_section_is_the_line_previous_implementation_followed_by_the_entire_implementation_of_the_marker_1(
      self) -> None:
    pass  # {{🍄 If `path_and_validator.old_path()` exists and contains an implementation for `marker`, that implementation gets included as the last section of the initial message. The section is the line "Previous implementation:", followed by the entire implementation (of the marker). (in CodeSpecsWorkflow._implement_marker)}}

  async def test_codespecsworkflow__implement_marker_the_only_done_command_argument_given_to_prepare_command_registry_is_implementation_variable_1(
      self) -> None:
    pass  # {{🍄 The only done command argument given to `prepare_command_registry` is `implementation_variable`. (in CodeSpecsWorkflow._implement_marker)}}

  async def test_codespecsworkflow__implement_marker_enables_caching_of_conversations_if_two_separate_instances_of_codespecsworkflow_have_this_method_called_for_the_same_path_and_validatordm_path_and_marker_the_2nd_call_reuses_the_outputs_from_the_first_1(
      self) -> None:
    pass  # {{🍄 Enables caching of conversations: if two separate instances of CodeSpecsWorkflow have this method called for the same `path_and_validator.dm_path` and marker, the 2nd call reuses the outputs from the first. (in CodeSpecsWorkflow._implement_marker)}}

  async def test_codespecsworkflow__implement_marker_doesnt_actually_overwrite_any_files_the_caller_does_1(
      self) -> None:
    pass  # {{🍄 Doesn't actually overwrite any files (the caller does). (in CodeSpecsWorkflow._implement_marker)}}


if __name__ == '__main__':
  unittest.main()
