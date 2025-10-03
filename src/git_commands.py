from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, VariableName
import subprocess
import sys
from file_access_policy import FileAccessPolicy
from enum import Enum, auto
from typing import Dict, Any
from validation import ValidationManager
import asyncio


class GitRepositoryState(Enum):
  NOT_A_GIT_REPO = auto()
  CLEAN = auto()
  NOT_CLEAN = auto()


class ResetFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy,
               validation_manager: ValidationManager | None) -> None:
    self.file_access_policy = file_access_policy
    self.validation_manager = validation_manager

  def Name(self) -> str:
    return self.Syntax().name

  async def run(self, inputs: dict[VariableName, Any]) -> CommandOutput:
    path: str = inputs[VariableName('path')]
    errors: list[str] = []

    try:
      process = await asyncio.create_subprocess_exec(
          "git",
          "checkout",
          path,
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE)
      stdout, stderr = await process.communicate()

      if process.returncode != 0:
        errors.append(stderr.decode().strip())

      if self.validation_manager:
        self.validation_manager.RegisterChange()
    except Exception as e:
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
                name=VariableName("path"),
                arg_type=ArgumentContentType.PATH_OUTPUT,
                description="Path to reset to original state.",
                required=True),
            Argument(
                name=VariableName("reason"),
                arg_type=ArgumentContentType.STRING,
                description="Brief (one or two sentences) explanation of why you are issuing this command (what you want to accomplish).",
                required=False)
        ])


async def CheckGitRepositoryState() -> GitRepositoryState:
  try:
    proc1 = await asyncio.create_subprocess_exec(
        "git",
        "rev-parse",
        "--is-inside-work-tree",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout1, stderr1 = await proc1.communicate()
    if proc1.returncode != 0:
      return GitRepositoryState.NOT_A_GIT_REPO

    cmds_to_check = [["git", "diff", "--quiet"],
                     ["git", "diff", "--cached", "--quiet"]]

    for cmd in cmds_to_check:
      proc = await asyncio.create_subprocess_exec(
          *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
      stdout, stderr = await proc.communicate()

      if proc.returncode != 0:
        return GitRepositoryState.NOT_CLEAN

    return GitRepositoryState.CLEAN

  except Exception:
    return GitRepositoryState.NOT_A_GIT_REPO
