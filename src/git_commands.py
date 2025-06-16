from agent_command import AgentCommand, CommandInput, CommandOutput
import subprocess


class ResetFileCommand(AgentCommand):

  def Name(self) -> str:
    return "reset_file"

  def GetDescription(self) -> str:
    return f"#{self.Name()} file0 [file1 file2 …]: Resets files to their original state. AI can use this to reset files it accidentally broke."

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    paths = command_input.arguments

    if not paths:
      return CommandOutput(
          output=[],
          errors=[f"No paths provided to {self.Name()}."],
          summary="Failed to reset files (no arguments)")

    errors = []
    for path in paths:
      try:
        subprocess.run(["git", "checkout", path], check=True)
      except subprocess.CalledProcessError as e:
        errors.append(str(e))

    if errors:
      return CommandOutput(
          output=[], errors=errors, summary="Error while resetting files")

    success_message = f"Reset files: {', '.join(paths)}"
    return CommandOutput(
        output=[success_message], errors=[], summary=success_message)
