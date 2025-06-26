from typing import Dict, Optional, Callable, List
from agent_command import AgentCommand
from agent_command_helpers import FormatHelp

from file_access_policy import FileAccessPolicy
from validation import ValidationManager
from validate_command import ValidateCommand
from read_file_command import ReadFileCommand
from list_files_command import ListFilesCommand
from write_file_command import WriteFileCommand
from search_file_command import SearchFileCommand
from select_commands import (
    SelectCommand,
    SelectOverwriteCommand,
    SelectionManager,
)
from select_python import SelectPythonCommand
from replace_python_command import ReplacePythonCommand
from git_commands import ResetFileCommand, CheckGitRepositoryState, GitRepositoryState
from task_command import TaskCommand, CommandOutput, TaskInformation
from help_command import HelpCommand
import sys


class UnknownCommandError(Exception):

  def __init__(self, unknown_commands: List[str]):
    self.unknown_commands = unknown_commands
    super().__init__(
        f"Unknown command(s): {', '.join(sorted(unknown_commands))}")


class CommandRegistry:

  def __init__(self) -> None:
    self.commands: Dict[str, AgentCommand] = {}

  def Register(self, command: AgentCommand):
    self.commands[command.Name()] = command

  def Get(self, name: str) -> Optional[AgentCommand]:
    return self.commands.get(name)

  def HelpText(self, command_names: Optional[List[str]] = None) -> str:
    if command_names is None:
      commands_to_process = list(self.commands.values())
    else:
      names_to_show = sorted(list(set(command_names)))
      if not names_to_show:
        return ""

      unknown_commands = [
          name for name in names_to_show if name not in self.commands
      ]
      if unknown_commands:
        raise UnknownCommandError(unknown_commands)

      commands_to_process = [self.commands[name] for name in names_to_show]

    return FormatHelp(commands_to_process)


def CreateCommandRegistry(file_access_policy: FileAccessPolicy,
                          validation_manager: Optional[ValidationManager],
                          start_new_task: Callable[[TaskInformation],
                                                   CommandOutput],
                          git_dirty_accept: bool = False,
                          can_write: bool = True,
                          can_start_tasks: bool = True) -> CommandRegistry:
  registry = CommandRegistry()
  help_command = HelpCommand()
  registry.Register(help_command)
  registry.Register(ReadFileCommand(file_access_policy))
  registry.Register(ListFilesCommand(file_access_policy))

  git_state = CheckGitRepositoryState()
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

  selection_manager = SelectionManager()
  if can_write:
    registry.Register(
        WriteFileCommand(file_access_policy, validation_manager,
                         selection_manager))

  registry.Register(SearchFileCommand(file_access_policy))

  for use_regex in [True, False]:
    registry.Register(
        SelectCommand(file_access_policy, selection_manager, use_regex))

  if can_write:
    registry.Register(
        SelectOverwriteCommand(selection_manager, validation_manager))

  registry.Register(SelectPythonCommand(file_access_policy, selection_manager))
  if can_write:
    registry.Register(
        ReplacePythonCommand(file_access_policy, validation_manager))

  if can_start_tasks:
    registry.Register(TaskCommand(start_new_task))

  help_command.SetAllCommands(registry.commands)

  return registry
