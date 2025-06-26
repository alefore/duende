from typing import Dict, Optional, List
from agent_command import AgentCommand
from agent_command_helpers import FormatHelp
from conversation import MultilineContent


class UnknownCommandError(Exception):

  def __init__(self, unknown_commands: List[str]):
    self.unknown_commands = unknown_commands
    super().__init__(
        f"Unknown command(s): {', '.join(sorted(unknown_commands))}")


class CommandRegistry:

  def __init__(self) -> None:
    self.commands: Dict[str, AgentCommand] = {}

  def Register(self, command: AgentCommand) -> None:
    self.commands[command.Name()] = command

  def Get(self, name: str) -> Optional[AgentCommand]:
    return self.commands.get(name)

  def list_all(self) -> list[str]:
    return list(self.commands.keys())

  def HelpText(self) -> MultilineContent:
    return FormatHelp(
        list(self.commands[name] for name in sorted(self.commands)))
