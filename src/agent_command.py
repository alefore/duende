from abc import ABC, abstractmethod
from typing import Any, Dict, List, NamedTuple, Optional
from collections import namedtuple
from enum import Enum, auto


class CommandOutput(NamedTuple):
  command_name: str
  output: List[str]
  errors: List[str]
  summary: str


class CommandInput(NamedTuple):
  command_name: str
  arguments: List[str] = []
  args: Dict[str, Any] = {}


class ArgumentContentType(Enum):
  IDENTIFIER = auto()
  OTHER = auto()
  PATH_INPUT = auto()
  PATH_INPUT_OUTPUT = auto()
  PATH_OUTPUT = auto()
  PATH_UNVALIDATED = auto()
  REGEX = auto()
  STRING = auto()


class Argument(NamedTuple):
  """Defines an argument with a name, type, and description."""
  name: str
  arg_type: ArgumentContentType
  description: str
  required: bool = True


class ArgumentMultiline(NamedTuple):
  """Defines a multiline argument with an indicator if it's required and a description."""
  required: bool = True
  description: str = ""


class CommandSyntax(NamedTuple):
  """Defines the syntax structure for an AgentCommand."""
  name: str = ''

  # A brief (one to three sentences) general description of the command.
  description: str = ''

  # MCP arguments
  arguments: List[Argument] = []

  output_type: ArgumentContentType = ArgumentContentType.STRING
  output_description: Optional[str] = None


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
  def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    pass
