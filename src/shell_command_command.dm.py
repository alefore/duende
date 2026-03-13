import asyncio
from dataclasses import dataclass
import logging
import os
import pathlib
from typing import Any, NewType

import agent_command
from agent_command import REASON_VARIABLE, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, VariableName
from pathbox import PathBox


class ShellCommandBase(agent_command.AgentCommand):

  def __init__(self, name: str, cwd: PathBox) -> None:
    self._name = name
    self._cwd = cwd

  def Name(self) -> str:
    return self.Syntax().name

  async def execute(self, command: str, input_cwd: pathlib.Path | None,
                    environment: dict[str, str] | None) -> CommandOutput:
    cwd: pathlib.Path = self._cwd.path
    if input_cwd:
      cwd = cwd / input_cwd
    try:
      logging.info(f"Executing shell command: {command}")
      process = await asyncio.create_subprocess_shell(
          command,
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE,
          cwd=cwd)

      stdout, stderr = await process.communicate()

      return CommandOutput(
          command_name=self._name,
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
          command_name=self._name,
          output="",
          errors=f"Shell command execution error: {e}",
          summary=f"Shell command execution failed: {e}")


class ShellCommandCommand(ShellCommandBase):

  def __init__(self, cwd: PathBox):
    return super().__init__(self.Syntax().name, cwd)

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

  async def run(
      self, inputs: dict[VariableName,
                         agent_command.VariableValue]) -> CommandOutput:
    command = inputs[VariableName("command")]
    input_path = inputs.get(VariableName('cwd'), '.')
    assert isinstance(command, str)
    assert isinstance(input_path, str)
    return await self.execute(command, pathlib.Path(input_path), None)


# The shell command string to be executed. Variables from `syntax` will be given
# as environment variables.
ShellCommandTemplate = NewType('ShellCommandTemplate', str)


@dataclass(frozen=True)
class ShellCommandTemplateConfig:
  syntax: CommandSyntax
  command: ShellCommandTemplate


@dataclass(frozen=True)
class ShellCommandTemplatesConfig:
  commands: dict[str, ShellCommandTemplateConfig]


def create_shell_commands_config(
    data: dict[str, Any]) -> ShellCommandTemplatesConfig:
  """Receives a JSON dictionary and turns it into a config.

  {{🦔 The dictionary has at most three entries: "arguments", "description",
       and "command".}}
  {{🦔 The value of `syntax.name` (outputs) come from the "arguments" dictionary
       keys.}}
  {{🦔 All `CommandSyntax` entries have `output_type` set to the default value.
       We don't allow `data` to override that.}}
  {{🦔 Raises ValueError exception if data contains unexpected keys (or if
       anything can't be parsed successfully).}}
  {{🦔 A ValueError exception due to unexpected keys mentions the set of
       expected keys.}}
  """
  raise NotImplementedError()  # {{🍄 create config}}


_DUENDE_SHELL_TEMPLATE = "DUENDE_SHELL_TEMPLATE_"


class ShellCommandTemplateCommand(ShellCommandBase):

  def __init__(self, cwd: PathBox, config: ShellCommandTemplateConfig) -> None:
    super().__init__(config.syntax.name, cwd)
    self._config = config

  def Syntax(self) -> CommandSyntax:
    """Returns a suitable syntax for this command.

    {{🦔 Return value includes `REASON_VARIABLE`.}}
    {{🦔 Return value includes all elements in `config.syntax`.}}
    """
    raise NotImplementedError()  # {{🍄 syntax}}

  def _prepare_environment(self,
                           inputs: agent_command.VariableMap) -> dict[str, str]:
    """Adds inputs from `config` to the environment and returns it.

    {{🦔 If an argument is not given (in `inputs`), asserts that the argument is
         not required and skips it (doesn't set it).}}
    {{🦔 The string _DUENDE_SHELL_TEMPLATE is prefixed to the names of the
         environment variables (output).}}
    {{🦔 The names of the environment variables (output) are all in uppercase
         (even if the config has lower-case names).}}
    """
    env = os.environ.copy()
    raise NotImplementedError()  # {{🍄 prepare environment}}

  async def run(self, inputs: agent_command.VariableMap) -> CommandOutput:
    return await self.execute(self._config.command, None,
                              self._prepare_environment(inputs))
