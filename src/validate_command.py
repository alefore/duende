import subprocess
from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument
from validation import ValidationManager
from typing import List, Any, Dict


class ValidateCommand(AgentCommand):

  def __init__(self, validation_manager: ValidationManager) -> None:
    self.validation_manager = validation_manager

  def Name(self) -> str:
    return self.Syntax().name

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        name="validate",
        description="Executes validation script to verify code integrity. Recommended to run this command after making changes."
    )

  async def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    result = await self.validation_manager.Validate()

    if not result.success:
      return CommandOutput(
          output="",
          errors=f"#{self.Name()} FAIL:\n" + result.error,
          summary="Validation script failed.",
          command_name=self.Name())

    return CommandOutput(
        output=f"#{self.Name()}: Success (all checks passed).",
        errors="",
        summary="Validation script succeeded.",
        command_name=self.Name())
