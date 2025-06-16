from typing import Dict, Optional
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
from git_commands import ResetFileCommand


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
    validation_manager: Optional[ValidationManager]) -> CommandRegistry:
  registry = CommandRegistry()
  registry.Register(ReadFileCommand(file_access_policy))
  registry.Register(ListFilesCommand(file_access_policy))
  registry.Register(ResetFileCommand(file_access_policy))

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

  return registry
