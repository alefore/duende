from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, VariableName
import logging
import asyncio
from typing import Any, Dict


class ShellCommandCommand(AgentCommand):

  def Name(self) -> str:
    return self.Syntax().name

  @classmethod
  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="shell_command",
        description="Executes a shell command and returns its stdout, stderr, and exit status.",
        arguments=[
            Argument(
                name=VariableName("command"),
                arg_type=ArgumentContentType.STRING,
                description="The shell command to execute.",
                required=True)
        ])

  async def run(self, inputs: Dict[VariableName, Any]) -> CommandOutput:
    command = inputs[VariableName("command")]
    logging.info(f"Executing shell command: {command}")

    try:
      process = await asyncio.create_subprocess_shell(
          command,
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE)

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
