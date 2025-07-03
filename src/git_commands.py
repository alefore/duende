from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
import subprocess
import sys
from file_access_policy import FileAccessPolicy
from enum import Enum, auto
from typing import List, Optional, Dict, Any
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
    return self.Syntax().name


  def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    path: str = inputs['path']
    errors: List[str] = []

    try:
      subprocess.run(["git", "checkout", path], check=True)
      if self.validation_manager:
        self.validation_manager.RegisterChange()
    except subprocess.CalledProcessError as e:
      errors.append(str(e))

    if errors:
      return CommandOutput(
          output="",
          errors="\n".join(errors),
          summary="Error while resetting files",
          command_name=self.Syntax().name)

    success_message = f"Reset file: {path}"
    return CommandOutput(
        output=success_message,
        errors="",
        summary=success_message,
        command_name=self.Syntax().name)

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        name="reset_file",
        description="Resets file to its original state. Use this if you accidentally broke a file.",
        arguments=[
            Argument(
                name="path",
                arg_type=ArgumentContentType.PATH_OUTPUT,
                description="Path to reset to original state.",
                required=True),
            Argument(
                name="reason",
                arg_type=ArgumentContentType.STRING,
                description="Brief (one or two sentences) explanation of why you are issuing this command (what you want to accomplish).",
                required=False)
        ])


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
