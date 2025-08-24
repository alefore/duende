import logging
import re
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Pattern

from agent_loop import AgentLoop
from agent_loop_options import AgentLoopOptions
from confirmation import ConfirmationState
from conversation import Conversation, ConversationId, ConversationFactory
from message import Message, ContentSection
from conversation_state import ConversationState
import review_utils
from agent_workflow_options import AgentWorkflowOptions


class AgentWorkflow(ABC):

  def __init__(self, options: AgentWorkflowOptions) -> None:
    self._options = options
    self._conversation_factory = options.conversation_factory

  @abstractmethod
  async def run(self) -> None:
    pass


class AgentWorkflowFactory(ABC):

  @abstractmethod
  def name(self) -> str:
    pass

  @abstractmethod
  async def new(self, agent_workflow_options: AgentWorkflowOptions,
                args: Dict[str, str]) -> AgentWorkflow:
    pass


class AgentWorkflowFactoryContainer:

  def __init__(self) -> None:
    self._workflow_factories: Dict[str, AgentWorkflowFactory] = {}

  def add(self, factory: AgentWorkflowFactory) -> None:
    assert factory.name() not in self._workflow_factories
    self._workflow_factories[factory.name()] = factory

  def factory_names(self) -> List[str]:
    return list(self._workflow_factories)

  def get(self, name: str) -> Optional[AgentWorkflowFactory]:
    return self._workflow_factories.get(name)
