import subprocess
from agent_command import AgentCommand, CommandInput, CommandOutput


class ValidateCommand(AgentCommand):

  def GetDescription(self) -> str:
    return ("Executes validation script to verify code integrity. "
            "Recommended to run this command after making changes. "
            "Usage: #validate")

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    validate_script = "agent/validate.sh"
    try:
      process = subprocess.run([validate_script],
                               capture_output=True,
                               text=True)
      if process.returncode != 0:
        return CommandOutput(
            output=[],
            errors=[f"Validation failed: {process.stderr.strip()}"],
            summary="Validation script failed.")
      return CommandOutput(
          output=["#validate: Success (all checks passed)."],
          errors=[],
          summary="Validation script succeeded.")
    except FileNotFoundError:
      return CommandOutput(
          output=[],
          errors=["Validation script not found."],
          summary="Validation script does not exist.")
    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"Error executing validation script: {str(e)}"],
          summary="Validation script execution error.")
