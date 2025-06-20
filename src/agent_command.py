from abc import ABC, abstractmethod
from typing import List, NamedTuple, Optional
from collections import namedtuple
from enum import Enum, auto


class CommandOutput(NamedTuple):
  output: List[str]
  errors: List[str]
  summary: str


class CommandInput(NamedTuple):
  command_name: str
  arguments: List[str]
  # multiline_content does not include newline characters.
  multiline_content: Optional[List[str]] = None


class ArgumentContentType(Enum):
  PATH = auto()
  REGEX = auto()
  IDENTIFIER = auto()
  STRING = auto()
  OTHER = auto()


class Argument(NamedTuple):
  """Defines an argument with a name, type, and description."""
  name: str
  arg_type: ArgumentContentType
  description: str


class ArgumentMultiline(NamedTuple):
  """Defines a multiline argument with an indicator if it's required and a description."""
  required: bool = True
  description: str = ""


class CommandSyntax(NamedTuple):
  """Defines the syntax structure for an AgentCommand."""

  # A brief (one to three sentences) general description of the command.
  description: str = ''

  # A list of required arguments for the command.
  required: List[Argument] = []

  # A list of optional positional arguments for the command. These come after the required arguments.
  optional: List[Argument] = []

  # An optional final argument that can be repeated multiple times (e.g., for commands accepting multiple files).
  repeatable_final: Optional[Argument] = None

  # An optional multiline argument for the command, if applicable.
  multiline: Optional[ArgumentMultiline] = None


class AgentCommand(ABC):

  @abstractmethod
  def Name(self) -> str:
    """Returns the name of the command."""
    pass

  @abstractmethod
  def GetDescription(self) -> str:
    """
    Returns a string describing what the command does and how to use it.
    This will be included in a prompt to the AI.
    """
    pass

  @abstractmethod
  def Execute(self, command_input: CommandInput) -> CommandOutput:
    """Executes the command with the given CommandInput."""
    pass

  @abstractmethod
  def Syntax(self) -> CommandSyntax:
    """
    Returns a CommandSyntax object describing the syntax of the command. 
    This provides an overview of how the command should be structured for proper usage.
    """
    pass
