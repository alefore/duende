from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from conversation import Conversation
from message import Message


class ConversationalAIConversation(ABC):

  @abstractmethod
  def SendMessage(self, message: Message) -> Message:
    """Sends a new message to the AI and returns the response."""
    pass


class ConversationalAI(ABC):

  @abstractmethod
  def StartConversation(
      self, conversation: Conversation) -> ConversationalAIConversation:
    pass
