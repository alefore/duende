from abc import ABC, abstractmethod
from typing import Any, Dict, List, NamedTuple, Optional
from collections import namedtuple
from enum import Enum, auto


class CommandOutput(NamedTuple):
  output: List[str]
  errors: List[str]
  summary: str
  # TODO: This shouldn't be Optional.
  command_name: Optional[str] = None


class CommandInput(NamedTuple):
  command_name: str
  arguments: List[str] = []
  args: Dict[str, Any] = {}
  # multiline_content does not include newline characters.
  multiline_content: Optional[List[str]] = None


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

  # A list of required arguments for the command.
  required: List[Argument] = []

  # A list of optional positional arguments for the command. These come after the required arguments.
  optional: List[Argument] = []

  # An optional final argument that can be repeated multiple times (e.g., for commands accepting multiple files).
  repeatable_final: Optional[Argument] = None

  # An optional multiline argument for the command, if applicable.
  multiline: Optional[ArgumentMultiline] = None

  output_type: ArgumentContentType = ArgumentContentType.STRING
  output_description: Optional[str] = None


class AgentCommand(ABC):

  @abstractmethod
  def Name(self) -> str:
    """Returns the name of the command."""
    pass

  @abstractmethod
  def Aliases(self) -> List[str]:
    """Returns a list of aliases for the command."""
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
