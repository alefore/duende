import subprocess
from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument
from validation import ValidationManager
from typing import List, Any, Dict


class ValidateCommand(AgentCommand):

  def __init__(self, validation_manager: ValidationManager) -> None:
    self.validation_manager = validation_manager

  def Name(self) -> str:
    return self.Syntax().name

  def Aliases(self) -> List[str]:
    return ["test", "check", "verify"]

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        name="validate",
        description="Executes validation script to verify code integrity. Recommended to run this command after making changes."
    )

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    assert False

  def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    result = self.validation_manager.Validate()

    if not result.success:
      return CommandOutput(
          output=[],
          errors=[f"#{self.Name()}_output FAIL << "] + result.error + ["#end"],
          summary="Validation script failed.",
          command_name=self.Name())

    return CommandOutput(
        output=[f"#{self.Name()}: Success (all checks passed)."],
        errors=[],
        summary="Validation script succeeded.",
        command_name=self.Name())
