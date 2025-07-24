import logging
import re
import sys
from abc import ABC, abstractmethod
from typing import List, Optional, Pattern

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
  def run(self) -> None:
    pass

  def get_conversation_by_id(self,
                             conversation_id: ConversationId) -> Conversation:
    return self._conversation_factory.Get(conversation_id)

  def get_all_conversations(self) -> List[Conversation]:
    return self._conversation_factory.GetAll()
