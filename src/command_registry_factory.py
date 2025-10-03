import asyncio

from typing import Dict, Callable, List
import sys

from agent_command import AgentCommand, CommandOutput
from agent_command_helpers import FormatHelp
from command_registry import CommandRegistry
from file_access_policy import FileAccessPolicy
from validation import ValidationManager
from validate_command import ValidateCommand
from read_file_command import ReadFileCommand
from list_files_command import ListFilesCommand
from write_file_command import WriteFileCommand
from search_file_command import SearchFileCommand
from select_commands import SelectCommand, SelectOverwriteCommand
from selection_manager import SelectionManager
from select_python import SelectPythonCommand
from replace_python_command import ReplacePythonCommand
from git_commands import ResetFileCommand, CheckGitRepositoryState, GitRepositoryState
from task_command import TaskInformation
from done_command import DoneCommand
from answer_command import AnswerCommand
from shell_command_command import ShellCommandCommand
import sys


def _create_base_registry(
    file_access_policy: FileAccessPolicy) -> CommandRegistry:
  registry = CommandRegistry()
  registry.Register(ReadFileCommand(file_access_policy))
  registry.Register(ListFilesCommand(file_access_policy))
  registry.Register(SearchFileCommand(file_access_policy))
  return registry


def create_ask_command_registry(
    file_access_policy: FileAccessPolicy) -> CommandRegistry:
  registry = CommandRegistry()
  registry.Register(ReadFileCommand(file_access_policy))
  registry.Register(ListFilesCommand(file_access_policy))
  registry.Register(SearchFileCommand(file_access_policy))
  registry.Register(AnswerCommand())
  return registry


async def create_command_registry(
    file_access_policy: FileAccessPolicy,
    validation_manager: ValidationManager | None,
    start_new_task: Callable[[TaskInformation], CommandOutput],
    git_dirty_accept: bool = False,
    can_write: bool = True,
    can_start_tasks: bool = True,
    shell_command_execution: bool = False) -> CommandRegistry:
  registry = _create_base_registry(file_access_policy)

  registry.Register(DoneCommand(arguments=[]))

  git_state = await CheckGitRepositoryState()
  if git_state == GitRepositoryState.CLEAN:
    registry.Register(ResetFileCommand(file_access_policy, validation_manager))
  elif git_state == GitRepositoryState.NOT_CLEAN:
    if git_dirty_accept:
      print(
          "Info: The repository has uncommitted changes; ignoring due to command-line flag --git-dirty-accept.",
          file=sys.stderr)
    else:
      print("Error: The repository has uncommitted changes.", file=sys.stderr)
      sys.exit(1)

  if validation_manager:
    registry.Register(ValidateCommand(validation_manager))

  if shell_command_execution:
    registry.Register(ShellCommandCommand())

  enable_select = False

  selection_manager = SelectionManager()
  if can_write:
    registry.Register(
        WriteFileCommand(validation_manager, selection_manager, None))

  if enable_select:
    for use_regex in [True, False]:
      registry.Register(
          SelectCommand(file_access_policy, selection_manager, use_regex))

    if can_write:
      registry.Register(
          SelectOverwriteCommand(selection_manager, validation_manager))

    registry.Register(
        SelectPythonCommand(file_access_policy, selection_manager))
    if can_write:
      registry.Register(
          ReplacePythonCommand(file_access_policy, validation_manager))

  #if can_start_tasks:
  #  registry.Register(TaskCommand(start_new_task))

  return registry


def CreateReviewCommandRegistry(
    file_access_policy: FileAccessPolicy) -> CommandRegistry:
  return _create_base_registry(file_access_policy)
