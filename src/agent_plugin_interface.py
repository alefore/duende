from abc import ABC, abstractmethod
from agent_command import AgentCommand
from agent_workflow import AgentWorkflow


class AgentPlugin(ABC):
  """Interface for Duende plugins."""

  @abstractmethod
  def get_commands(self) -> list[AgentCommand]:
    """Returns a list of AgentCommand implementations provided by the plugin."""
    pass

  @abstractmethod
  def get_workflows(self) -> list[AgentWorkflow]:
    """Returns a list of AgentWorkflow implementations provided by the plugin."""
    pass
