from typing import Dict, List

from conversation import MultilineContent
from command_registry import CommandRegistry
from agent_command import (AgentCommand, Argument, ArgumentContentType,
                           CommandInput, CommandOutput, CommandSyntax)
from agent_command_helpers import FormatHelp


class HelpCommand(AgentCommand):

  def __init__(self, command_registry: CommandRegistry) -> None:
    self.command_registry: CommandRegistry = command_registry

  def Name(self) -> str:
    return "help"

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        description="Shows help for a given command. If none is given, for all commands.",
        repeatable_final=Argument(
            name="command",
            arg_type=ArgumentContentType.STRING,
            description="The command to get help for."))

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    command_names = sorted(
        set(command_input.arguments or
            [c.Name() for c in self.command_registry.list_all()]))

    valid_commands: List[AgentCommand] = []
    unknown_commands: MultilineContent = []
    for name in command_names:
      command = self.command_registry.Get(name)
      if command:
        valid_commands.append(command)
      else:
        unknown_commands.append(name)

    errors: MultilineContent = []
    if unknown_commands:
      errors.append(
          f"#{self.Name()}: Unknown command(s): {', '.join(unknown_commands)}")

    return CommandOutput(
        output=FormatHelp(valid_commands),
        errors=errors,
        summary=self._summary(valid_commands, unknown_commands))

  def _summary(self, valid_commands, unknown_commands):
    summary_parts = []
    if valid_commands:
      valid_names = sorted(c.Name() for c in valid_commands)
      summary_parts.append(f"Help for: {', '.join(valid_names)}.")
    if unknown_commands:
      summary_parts.append(
          f"Unknown command(s): {', '.join(unknown_commands)}.")
    return " ".join(summary_parts)
