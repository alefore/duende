from typing import Dict, Optional, List, Set
from agent_command import AgentCommand
from agent_command_helpers import FormatHelp
from conversation import MultilineContent


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
    self.canonical_names: Set[str] = set()

  def Register(self, command: AgentCommand) -> None:
    name = command.Name()
    all_new_names = {name}.union(command.Aliases())

    clashes = all_new_names.intersection(self.commands)
    if clashes:
      raise CommandRegistrationError(
          f"Name/alias clash for: {', '.join(sorted(clashes))}")

    self.canonical_names.add(name)
    for n in all_new_names:
      self.commands[n] = command

  def Get(self, name: str) -> Optional[AgentCommand]:
    return self.commands.get(name)

  def list_all(self) -> List[str]:
    return sorted(self.canonical_names)

  def HelpText(self) -> MultilineContent:
    return FormatHelp([self.commands[name] for name in self.list_all()])

  def GetCommands(self) -> List[AgentCommand]:
    return [self.commands[c] for c in self.canonical_names]
