import subprocess
from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax
from validation import ValidationManager


class ValidateCommand(AgentCommand):

  def __init__(self, validation_manager: ValidationManager) -> None:
    self.validation_manager = validation_manager

  def Name(self) -> str:
    return "validate"

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        description="Executes validation script to verify code integrity. Recommended to run this command after making changes."
    )

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    result = self.validation_manager.Validate()

    if not result.success:
      return CommandOutput(
          output=[],
          errors=[f"#validate_output FAIL << "] + result.error + ["#end"],
          summary="Validation script failed.")

    return CommandOutput(
        output=["#validate: Success (all checks passed)."],
        errors=[],
        summary="Validation script succeeded.")
