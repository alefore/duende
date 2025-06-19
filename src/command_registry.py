from typing import Dict, Optional, Callable
from agent_command import AgentCommand

from file_access_policy import FileAccessPolicy
from validation import ValidationManager
from validate_command import ValidateCommand
from read_file_command import ReadFileCommand
from list_files_command import ListFilesCommand
from write_file_command import WriteFileCommand
from search_file_command import SearchFileCommand
from select_commands import (
    SelectTextCommand,
    SelectOverwriteCommand,
    SelectionManager,
)
from select_python import SelectPythonCommand
from replace_python_command import ReplacePythonCommand
from git_commands import ResetFileCommand, CheckGitRepositoryState, GitRepositoryState
from task_command import TaskCommand, CommandOutput, TaskInformation
import sys


class CommandRegistry:

  def __init__(self) -> None:
    self.commands: Dict[str, AgentCommand] = {}

  def Register(self, command: AgentCommand):
    self.commands[command.Name()] = command

  def Get(self, name: str) -> Optional[AgentCommand]:
    return self.commands.get(name)

  def HelpText(self) -> str:
    return '\n'.join(cmd.GetDescription() for cmd in self.commands.values())


def CreateCommandRegistry(
    file_access_policy: FileAccessPolicy,
    validation_manager: Optional[ValidationManager],
    start_new_task: Callable[[TaskInformation],
                             CommandOutput]) -> CommandRegistry:
  registry = CommandRegistry()
  registry.Register(ReadFileCommand(file_access_policy))
  registry.Register(ListFilesCommand(file_access_policy))

  git_state = CheckGitRepositoryState()

  if git_state == GitRepositoryState.CLEAN:
    registry.Register(ResetFileCommand(file_access_policy))
  elif git_state == GitRepositoryState.NOT_CLEAN:
    print("Error: The repository has uncommitted changes.", file=sys.stderr)
    sys.exit(1)

  if validation_manager:
    registry.Register(ValidateCommand(validation_manager))

  selection_manager = SelectionManager()
  registry.Register(
      WriteFileCommand(file_access_policy, validation_manager,
                       selection_manager))
  registry.Register(SearchFileCommand(file_access_policy))

  registry.Register(SelectTextCommand(file_access_policy, selection_manager))
  registry.Register(
      SelectOverwriteCommand(selection_manager, validation_manager))

  registry.Register(SelectPythonCommand(file_access_policy, selection_manager))
  registry.Register(
      ReplacePythonCommand(file_access_policy, validation_manager))

  registry.Register(TaskCommand(start_new_task))

  return registry
