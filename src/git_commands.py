from agent_command import AgentCommand, CommandInput, CommandOutput
import subprocess
import sys
from file_access_policy import FileAccessPolicy


class ResetFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy) -> None:
    self.file_access_policy = file_access_policy

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

    errors = [
        f"Access to '{path}' is not allowed by the policy." for path in paths
        if not self.file_access_policy.allow_access(path)
    ]

    if errors:
      return CommandOutput(
          output=[],
          errors=errors,
          summary="Error while resetting files due to access policy")

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


def EnsureGitRepoIsClean() -> bool:
  try:
    # Check if we are inside a git repository
    subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                   check=True,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)

    # Check if the git repository is clean (no changes)
    result = subprocess.run(["git", "status", "--porcelain"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    if result.stdout != b'':
      print("Error: The repository has uncommitted changes.", file=sys.stderr)
      sys.exit(1)

    return True

  except subprocess.CalledProcessError:
    return False
