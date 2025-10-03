from typing import Any
import logging

from agent_command import AgentCommand, CommandOutput, CommandSyntax, ArgumentContentType, Argument, VariableName
from validation import ValidationManager, ValidationResult


class DoneCommand(AgentCommand):

  def __init__(self,
               arguments: list[Argument],
               validation_manager: ValidationManager | None = None) -> None:
    self._validation_manager = validation_manager
    self._arguments = arguments

  def Name(self) -> str:
    return self.Syntax().name

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="done",
        description="Signals that the current task is completed.",
        arguments=self._arguments,
    )

  async def run(self, inputs: dict[VariableName, Any]) -> CommandOutput:
    logging.info("Done command runs!")
    for k in self._arguments:
      if k.required:
        assert k.name in inputs

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
          output_variables=inputs,
          summary=f"Validation succeeded.",
          task_done=True,
      )
