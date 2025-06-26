from typing import TYPE_CHECKING

from agent_command import (AgentCommand, Argument, ArgumentContentType,
                           CommandInput, CommandOutput, CommandSyntax)
from agent_command_helpers import HelpText as RenderHelpText

if TYPE_CHECKING:
  from command_registry import CommandRegistry


class HelpCommand(AgentCommand):

  def __init__(self, command_registry: "CommandRegistry"):
    self.command_registry = command_registry

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
    if not command_input.arguments:
      return CommandOutput(
          output=[self.command_registry.HelpText()],
          errors=[],
          summary="Displayed help for all commands.")

    all_descriptions = []
    errors = []
    for name in command_input.arguments:
      command = self.command_registry.Get(name)
      if command:
        all_descriptions.append(
            RenderHelpText(command.Name(), command.Syntax()))
      else:
        errors.append(f"#{self.Name()}: Unknown command '{name}'")

    summary = f"Displayed help for: {', '.join(command_input.arguments)}."
    output = ["\n\n".join(all_descriptions)] if all_descriptions else []

    return CommandOutput(output=output, errors=errors, summary=summary)
