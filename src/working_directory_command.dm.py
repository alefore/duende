from dataclasses import dataclass
import logging
import pathlib

from agent_command import AgentCommand, CommandOutput, CommandSyntax, Argument, ArgumentContentType, PATH_VARIABLE_NAME, REASON_VARIABLE, VariableMap, VariableName
from file_access_policy import FileAccessPolicy


@dataclass
class PathBox:
  path = pathlib.Path('.')

  def __truediv__(self, other: pathlib.Path | str) -> pathlib.Path:
    return self.path / other


class ChangeWorkingDirectoryCommand(AgentCommand):

  def __init__(self, working_directory: PathBox) -> None:
    raise NotImplementedError()  # {{🍄 init method}}

  def Name(self) -> str:
    return self.Syntax().name

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        name="chdir",
        description="Changes the current working directory (affecting agent commands).",
        arguments=[
            REASON_VARIABLE,
            Argument(
                name=PATH_VARIABLE_NAME,
                arg_type=ArgumentContentType.PATH_INPUT,
                description="New working directory.",
                required=False)
        ])

  async def run(self, inputs: VariableMap) -> CommandOutput:
    """Assigns input `path` to `self._working_directory`."""
    raise NotImplementedError()  # {{🍄 run method}}
