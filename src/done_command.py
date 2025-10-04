import abc
import logging

from agent_command import AgentCommand, CommandOutput, CommandSyntax, ArgumentContentType, Argument, VariableMap, VariableName
from validation import ValidationManager, ValidationResult


class DoneValuesValidator(abc.ABC):

  @abc.abstractmethod
  async def validate(self, inputs: VariableMap) -> ValidationResult:
    pass


class DoneCommand(AgentCommand):

  def __init__(self,
               arguments: list[Argument],
               validation_manager: ValidationManager | None = None,
               values_validator: DoneValuesValidator | None = None) -> None:
    self._validation_manager = validation_manager
    self._values_validator = values_validator
    self._arguments = arguments

  def Name(self) -> str:
    return self.Syntax().name

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="done",
        description="Signals that the current task is completed.",
        arguments=self._arguments,
    )

  def _error_to_command_output(self, error: ValidationResult) -> CommandOutput:
    return CommandOutput(
        self.Name(),
        output=error.output,
        errors=error.error,
        summary=f"Validation failed.",
        task_done=False,
    )

  async def run(self, inputs: VariableMap) -> CommandOutput:
    logging.info("Done command runs!")
    for k in self._arguments:
      if k.required:
        assert k.name in inputs

    if self._validation_manager:
      result = await self._validation_manager.Validate()
      if not result.success:
        return self._error_to_command_output(result)

    if self._values_validator:
      result = await self._values_validator.validate(inputs)
      if not result.success:
        return self._error_to_command_output(result)

    return CommandOutput(
        self.Name(),
        "",
        "",
        "Task completed.",
        output_variables=inputs,
        task_done=True)
