import logging
import asyncio
import pathlib
from typing import Any

from agent_command import REASON_VARIABLE, AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, VariableName
from pathbox import PathBox


class ShellCommandCommand(AgentCommand):

  def __init__(self, cwd: PathBox) -> None:
    self._cwd = cwd

  def Name(self) -> str:
    return self.Syntax().name

  @classmethod
  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="shell_command",
        description="Executes a shell command and returns its stdout, stderr, and exit status.",
        arguments=[
            REASON_VARIABLE,
            Argument(
                name=VariableName("command"),
                arg_type=ArgumentContentType.STRING,
                description="The shell command to execute.",
                required=True),
            Argument(
                name=VariableName("cwd"),
                arg_type=ArgumentContentType.STRING,
                description="An optional directory to change into before running this command.",
                required=False)
        ])

  async def run(self, inputs: dict[VariableName, Any]) -> CommandOutput:
    command = inputs[VariableName("command")]
    logging.info(f"Executing shell command: {command}")

    cwd = self._cwd / pathlib.Path(inputs.get(VariableName('cwd'), '.'))
    try:
      process = await asyncio.create_subprocess_shell(
          command,
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE,
          cwd=cwd)

      stdout, stderr = await process.communicate()

      return CommandOutput(
          command_name=self.Syntax().name,
          output=str({
              "stdout": stdout.decode().strip(),
              "stderr": stderr.decode().strip(),
              "exit_status": process.returncode
          }),
          errors="" if not stderr else stderr.decode().strip(),
          summary=f"Shell command executed with exit status {process.returncode}."
          + (" Stderr not empty." if stderr else ""))

    except Exception as e:
      return CommandOutput(
          command_name=self.Syntax().name,
          output="",
          errors=f"Shell command execution error: {e}",
          summary=f"Shell command execution failed: {e}")
