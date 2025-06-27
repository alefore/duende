from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
import subprocess
import sys
from file_access_policy import FileAccessPolicy
from enum import Enum, auto
from typing import List, Optional
from validation import ValidationManager


class GitRepositoryState(Enum):
  NOT_A_GIT_REPO = auto()
  CLEAN = auto()
  NOT_CLEAN = auto()


class ResetFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy,
               validation_manager: Optional[ValidationManager]) -> None:
    self.file_access_policy = file_access_policy
    self.validation_manager = validation_manager

  def Name(self) -> str:
    return "reset_file"

  def Aliases(self) -> List[str]:
    return ["revert", "undo"]

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    paths = command_input.arguments
    errors: List[str] = []
    successful_resets = 0

    for path in paths:
      try:
        subprocess.run(["git", "checkout", path], check=True)
        successful_resets += 1
      except subprocess.CalledProcessError as e:
        errors.append(str(e))

    if successful_resets > 0 and self.validation_manager:
      self.validation_manager.RegisterChange()

    if errors:
      return CommandOutput(
          output=[], errors=errors, summary="Error while resetting files")

    success_message = f"Reset files: {', '.join(paths)}"
    return CommandOutput(
        output=[success_message], errors=[], summary=success_message)

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        description="Resets files to their original state. AI can use this to reset files it accidentally broke.",
        repeatable_final=Argument(
            name="path",
            arg_type=ArgumentContentType.PATH_OUTPUT,
            description="Path to reset to original state."))


def CheckGitRepositoryState() -> GitRepositoryState:
  try:
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
