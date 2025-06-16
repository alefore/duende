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

COMMAND_PREFIX = "#"


class CommandRegistry:

  def __init__(self) -> None:
    self.commands: Dict[str, AgentCommand] = {}

  def Register(self, name: str, command: AgentCommand):
    self.commands[name] = command

  def Get(self, name: str) -> Optional[AgentCommand]:
    return self.commands.get(name)

  def HelpText(self) -> str:
    return '\n'.join(f"{COMMAND_PREFIX}{name}: {cmd.GetDescription()}"
                     for name, cmd in self.commands.items())


def CreateCommandRegistry(
    file_access_policy: FileAccessPolicy,
    validation_manager: Optional[ValidationManager]) -> CommandRegistry:
  registry = CommandRegistry()
  registry.Register("read_file", ReadFileCommand(file_access_policy))
  registry.Register("list_files", ListFilesCommand(file_access_policy))

  if validation_manager:
    registry.Register("validate", ValidateCommand(validation_manager))

  selection_manager = SelectionManager()
  registry.Register(
      "write_file",
      WriteFileCommand(file_access_policy, validation_manager,
                       selection_manager))
  registry.Register("search", SearchFileCommand(file_access_policy))

  registry.Register("select",
                    SelectTextCommand(file_access_policy, selection_manager))
  registry.Register(
      "select_overwrite",
      SelectOverwriteCommand(selection_manager, validation_manager))

  registry.Register("select_python",
                    SelectPythonCommand(file_access_policy, selection_manager))

  return registry
