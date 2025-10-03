from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import NamedTuple, NewType
from collections import namedtuple
from enum import Enum, auto

VariableName = NewType("VariableName", str)
VariableValueInt = NewType("VariableValueInt", int)
VariableValueStr = NewType("VariableValueStr", str)
VariableValue = VariableValueInt | VariableValueStr
VariableMap = NewType("VariableMap", dict[VariableName, VariableValue])


class CommandOutput(NamedTuple):
  command_name: str
  output: str
  errors: str
  summary: str
  output_variables: dict[VariableName, VariableValue] = {}
  task_done: bool = False
  thought_signature: bytes | None = None


class CommandInput(NamedTuple):
  command_name: str
  args: VariableMap = VariableMap({})
  # Args that are computed by the command (before `run`).
  # They are mostly used to communicate additional debugging information
  # to the frontend.
  derived_args: VariableMap = VariableMap({})
  thought_signature: bytes | None = None


class ArgumentContentType(Enum):
  IDENTIFIER = auto()
  OTHER = auto()
  PATH_INPUT = auto()
  PATH_INPUT_OUTPUT = auto()
  PATH_OUTPUT = auto()
  PATH_UNVALIDATED = auto()
  REGEX = auto()
  STRING = auto()
  INTEGER = auto()


class Argument(NamedTuple):
  """Defines an argument with a name, type, and description."""
  name: VariableName
  arg_type: ArgumentContentType
  description: str
  required: bool = True


class CommandSyntax(NamedTuple):
  """Defines the syntax structure for an AgentCommand."""
  name: str = ''

  # A brief (one to three sentences) general description of the command.
  description: str = ''

  # MCP arguments
  arguments: list[Argument] = []

  output_type: ArgumentContentType = ArgumentContentType.STRING
  output_description: str | None = None


class AgentCommand(ABC):

  @abstractmethod
  def Name(self) -> str:
    """Returns the name of the command."""
    pass

  @abstractmethod
  def Syntax(self) -> CommandSyntax:
    """
    Returns a CommandSyntax object describing the syntax of the command. 
    This provides an overview of how the command should be structured for proper usage.
    """
    pass

  @abstractmethod
  async def run(self, inputs: VariableMap) -> CommandOutput:
    pass

  async def derive_args(self, inputs: VariableMap) -> VariableMap:
    """
    Computes additional, display-only properties for the command.
    These properties are attached to the CommandInput object.
    """
    return VariableMap({})
