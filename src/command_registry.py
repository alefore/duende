from typing import Dict, Optional, List, Set
from agent_command import AgentCommand
from agent_command_helpers import FormatHelp


class UnknownCommandError(Exception):

  def __init__(self, unknown_commands: List[str]):
    self.unknown_commands = unknown_commands
    super().__init__(
        f"Unknown command(s): {', '.join(sorted(unknown_commands))}")


class CommandRegistrationError(Exception):
  """Raised when there is a name or alias clash during command registration."""
  pass


class CommandRegistry:

  def __init__(self) -> None:
    self.commands: Dict[str, AgentCommand] = {}

  def Register(self, command: AgentCommand) -> None:
    name = command.Name()
    if name in self.commands:
      raise CommandRegistrationError(
          f"Command with name {name} already registered.")

    self.commands[name] = command

  def Get(self, name: str) -> Optional[AgentCommand]:
    return self.commands.get(name)

  def list_all(self) -> List[str]:
    return sorted(self.commands.keys())

  def HelpText(self) -> str:
    return FormatHelp([self.commands[name] for name in self.list_all()])

  def GetCommands(self) -> List[AgentCommand]:
    return list(self.commands.values())
