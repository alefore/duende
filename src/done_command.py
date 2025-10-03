from typing import List, Any, Dict, Optional
import logging

from agent_command import AgentCommand, CommandOutput, CommandSyntax, ArgumentContentType, Argument
from validation import ValidationManager, ValidationResult


class DoneCommand(AgentCommand):

  def __init__(self,
               validation_manager: Optional[ValidationManager] = None) -> None:
    self._validation_manager = validation_manager

  def Name(self) -> str:
    return self.Syntax().name

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="done",
        description="Signals that the current task is completed.",
        arguments=[],
    )

  async def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    logging.info("Done command runs!")
    if not self._validation_manager:
      return CommandOutput(
          self.Name(), "", "", "Task completed.", task_done=True)

    validation_result: ValidationResult = await self._validation_manager.Validate(
    )
    if not validation_result.success:
      return CommandOutput(
          self.Name(),
          output=validation_result.output,
          errors=validation_result.error,
          summary=f"Validation failed.",
          task_done=False,
      )
    else:
      return CommandOutput(
          self.Name(),
          output=validation_result.output,
          errors="",
          summary=f"Validation succeeded.",
          task_done=True,
      )
