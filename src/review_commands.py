import logging
from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
from typing import Callable, List, Optional, Dict, Any


class SuggestCommand(AgentCommand):

  def __init__(self, add_suggestion_callback: Callable[[str, str], None]):
    self._add_suggestion_callback = add_suggestion_callback

  def Name(self) -> str:
    return self.Syntax().name

  def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    suggestion_content = inputs["suggestion_content"]
    justification = inputs["justification"]

    if not suggestion_content:
      return CommandOutput(
          output=[],
          errors=["#suggest requires non-empty content."],
          summary="Suggestion failed: no content.",
          command_name=self.Syntax().name)

    self._add_suggestion_callback(suggestion_content, justification)
    logging.info(
        f"Suggestion recorded: '{suggestion_content[:50]}…' with justification '{justification[:50]}…'"
    )
    return CommandOutput(
        output=["Suggestion recorded successfully."],
        errors=[],
        summary="Suggestion recorded.",
        command_name=self.Syntax().name)

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="suggest",
        description="Records a suggestion for the code changes. Use with multi-line content to provide detailed suggestions.",
        arguments=[
            Argument(
                name="suggestion_content",
                arg_type=ArgumentContentType.STRING,
                description="The detailed suggestion for the code changes.",
                required=True),
            Argument(
                name="justification",
                arg_type=ArgumentContentType.STRING,
                description="The AI *must* justify why this suggestion is being issued (why is it related to the goal of the review). You should only issue suggestions directly related to the specific review task.",
                required=True)
        ])
