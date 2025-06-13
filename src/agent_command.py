from abc import ABC, abstractmethod
from typing import List, NamedTuple, Optional


class CommandOutput(NamedTuple):
  output: List[str]
  errors: List[str]
  summary: str


class CommandInput(NamedTuple):
  command_name: str
  arguments: List[str]
  # multiline_content does not include newline characters.
  multiline_content: Optional[List[str]] = None


class AgentCommand(ABC):

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
