import asyncio
import aiofiles
import dataclasses
import json
import pathlib
from typing import Any, Callable
import sys

from agent_command import AgentCommand, CommandOutput
from agent_command_helpers import FormatHelp
from command_registry import CommandRegistry
from file_access_policy import create_file_access_policy, create_file_access_policy_config, load_file_access_policy, FileAccessPolicyConfig, FileAccessPolicy  # , PermissiveFileAccessPolicy
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


@dataclasses.dataclass(frozen=True)
class CommandRegistryWriteConfig:
  # If `None`, defaults to top-level config. Otherwise, both configs must allow
  # access.
  file_access_policy: FileAccessPolicyConfig | None


@dataclasses.dataclass(frozen=True)
class CommandRegistryConfig:
  # If `None`, no file access is given.
  file_access_policy: FileAccessPolicyConfig | None

  # If present, signifies that write access is allowed.
  writes: CommandRegistryWriteConfig | None = None

  allow_shell: bool = False


def create_command_registry_config(
    data: dict[str, Any]) -> CommandRegistryConfig:
  """Receives a JSON dictionary and turns it into a config.

  Raises ValueError exception if data contains unexpected keys (or if anything
  can't be parsed successfully)."""
  raise NotImplementedError()  # {{🍄 create config}}


async def load_command_registry_config(
    path: pathlib.Path) -> CommandRegistryConfig:
  """Loads the configuration from JSON file in `path`."""
  raise NotImplementedError()  # {{🍄 load config}}


async def create_command_registry(
    config: CommandRegistryConfig,
    validation_manager: ValidationManager | None,
    start_new_task: Callable[[TaskInformation], CommandOutput],
    git_dirty_accept: bool = False,
    can_start_tasks: bool = True) -> CommandRegistry:

  assert config.file_access_policy
  file_access_policy = create_file_access_policy(config.file_access_policy)
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

  if config.allow_shell:
    registry.Register(ShellCommandCommand())

  enable_select = False

  selection_manager = SelectionManager()
  if config.writes:
    # TODO: Figure out how to pass the file access policy.
    registry.Register(
        WriteFileCommand(validation_manager, selection_manager, None))

  if enable_select:
    for use_regex in [True, False]:
      registry.Register(
          SelectCommand(file_access_policy, selection_manager, use_regex))

    if config.writes:
      registry.Register(
          SelectOverwriteCommand(selection_manager, validation_manager))

    registry.Register(
        SelectPythonCommand(file_access_policy, selection_manager))
    if config.writes:
      registry.Register(
          ReplacePythonCommand(file_access_policy, validation_manager))

  #if can_start_tasks:
  #  registry.Register(TaskCommand(start_new_task))

  return registry


def CreateReviewCommandRegistry(
    file_access_policy: FileAccessPolicy) -> CommandRegistry:
  return _create_base_registry(file_access_policy)
