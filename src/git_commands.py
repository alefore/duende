from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
import subprocess
import sys
from file_access_policy import FileAccessPolicy
from enum import Enum, auto


class GitRepositoryState(Enum):
  NOT_A_GIT_REPO = auto()
  CLEAN = auto()
  NOT_CLEAN = auto()


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

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        repeatable_final=Argument(
            name="path",
            arg_type=ArgumentContentType.PATH_OUTPUT,
            description="Path to reset to original state."))


def CheckGitRepositoryState() -> GitRepositoryState:
  try:
    # Check if we are inside a git repository
    subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                   check=True,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)

    for cmd in [["git", "diff", "--quiet"],
                ["git", "diff", "--cached", "--quiet"]]:
      result = subprocess.run(
          cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

      if result.returncode != 0:
        return GitRepositoryState.NOT_CLEAN

    return GitRepositoryState.CLEAN

  except subprocess.CalledProcessError:
    return GitRepositoryState.NOT_A_GIT_REPO
