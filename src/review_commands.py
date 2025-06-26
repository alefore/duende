import logging
from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, ArgumentMultiline
from conversation import MultilineContent
from typing import Callable, List, Optional


class SuggestCommand(AgentCommand):

  def __init__(self, add_suggestion_callback: Callable[[MultilineContent],
                                                       None]):
    self._add_suggestion_callback = add_suggestion_callback

  def Name(self) -> str:
    return "suggest"

  def Execute(self, cmd_input: CommandInput) -> CommandOutput:
    if not cmd_input.multiline_content:
      return CommandOutput(
          output=[],
          errors=["#suggest requires non-empty multiline content."],
          summary="Suggestion failed: no content.")

    self._add_suggestion_callback(cmd_input.multiline_content)
    logging.info(
        f"Suggestion recorded (first 50 chars): '{'\n'.join(cmd_input.multiline_content)[:50]}...'"
    )
    return CommandOutput(
        output=["Suggestion recorded successfully."],
        errors=[],
        summary="Suggestion recorded.")

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        description="Records a suggestion for the code changes. Use with multi-line content to provide detailed suggestions.",
        multiline=ArgumentMultiline(
            required=True,
            description="The detailed suggestion for the code changes."))
