from abc import ABC, abstractmethod
from typing import List, Dict, Any
from conversation import Conversation
from message import Message


class ConversationalAIConversation(ABC):

  @abstractmethod
  async def SendMessage(self, message: Message) -> Message:
    """Sends a new message to the AI and returns the response."""
    pass


class ConversationalAI(ABC):

  @abstractmethod
  def StartConversation(
      self, conversation: Conversation) -> ConversationalAIConversation:
    pass
