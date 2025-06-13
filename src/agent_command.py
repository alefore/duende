from abc import ABC, abstractmethod
from typing import List, NamedTuple, Optional


class CommandInput(NamedTuple):
  command_name: str
  arguments: List[str]
  multiline_content: Optional[str] = None


class AgentCommand(ABC):

  @abstractmethod
  def GetDescription(self) -> str:
    """
        Returns a string describing what the command does and how to use it.
        This will be included in a prompt to the AI.
        """
    pass

  @abstractmethod
  def Execute(self, command_input: CommandInput) -> str:
    """Executes the command with the given CommandInput."""
    pass
