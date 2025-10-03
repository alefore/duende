from typing import Dict, Set
from agent_command import AgentCommand
from agent_command_helpers import FormatHelp


class UnknownCommandError(Exception):

  def __init__(self, unknown_commands: list[str]):
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

  def Get(self, name: str) -> AgentCommand | None:
    return self.commands.get(name)

  def list_all(self) -> list[str]:
    return sorted(self.commands.keys())

  def HelpText(self) -> str:
    return FormatHelp([self.commands[name] for name in self.list_all()])

  def GetCommands(self) -> list[AgentCommand]:
    return list(self.commands.values())

  def available_commands_str(self) -> str:
    return "Available MCP functions: " + ', '.join(self.list_all())
