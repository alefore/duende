from typing import Dict, List

from agent_command import (AgentCommand, Argument, ArgumentContentType,
                           CommandInput, CommandOutput, CommandSyntax)
from agent_command_helpers import FormatHelp


class HelpCommand(AgentCommand):

  def __init__(self):
    self.all_commands: Dict[str, AgentCommand] = {}

  def SetAllCommands(self, all_commands: Dict[str, AgentCommand]):
    self.all_commands = all_commands

  def Name(self) -> str:
    return "help"

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        description="Shows a list of all available commands, or details for specific commands.",
        repeatable_final=Argument(
            name="command",
            arg_type=ArgumentContentType.STRING,
            description="The command to get help for. Can be specified multiple times."
        ))

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    command_names = command_input.arguments
    if not command_names:
      help_text = FormatHelp(list(self.all_commands.values()))
      return CommandOutput(
          output=[help_text],
          errors=[],
          summary="Displayed help for all commands.")

    names_to_show = sorted(list(set(command_names)))

    valid_commands: List[AgentCommand] = []
    unknown_commands: List[str] = []
    for name in names_to_show:
      command = self.all_commands.get(name)
      if command:
        valid_commands.append(command)
      else:
        unknown_commands.append(name)

    errors = []
    if unknown_commands:
      errors.append(
          f"#{self.Name()}: Unknown command(s): {', '.join(unknown_commands)}")

    output = []
    if valid_commands:
      output.append(FormatHelp(valid_commands))

    summary_parts = []
    if valid_commands:
      valid_names = sorted([c.Name() for c in valid_commands])
      summary_parts.append(f"Displayed help for: {', '.join(valid_names)}.")
    if unknown_commands:
      summary_parts.append(
          f"Unknown command(s): {', '.join(unknown_commands)}.")
    summary = " ".join(summary_parts)

    return CommandOutput(output=output, errors=errors, summary=summary)
