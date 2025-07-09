from abc import ABC, abstractmethod
from typing import Dict, Optional, Callable
import threading
import queue

from conversation import ConversationId


class ConfirmationManager(ABC):

  @abstractmethod
  def RequireConfirmation(self, conversation_id: ConversationId,
                          message: str) -> Optional[str]:
    """Blocks execution until confirmation is given, returning additional guidance if provided by the user."""
    pass


class CLIConfirmationManager(ConfirmationManager):

  def RequireConfirmation(self, conversation_id: ConversationId,
                          message: str) -> Optional[str]:
    return input(message).strip()


class AsyncConfirmationManager(ConfirmationManager):

  def __init__(
      self,
      on_confirmation_requested: Optional[Callable[[ConversationId, str],
                                                   None]] = None
  ) -> None:
    self.confirm_queue: Dict[ConversationId, queue.Queue[str]] = {}
    self.message_lock = threading.Lock()
    self.current_message: Dict[ConversationId, str] = {}
    self.on_confirmation_requested = on_confirmation_requested

  def RequireConfirmation(self, conversation_id: ConversationId,
                          message: str) -> Optional[str]:
    with self.message_lock:
      if conversation_id not in self.confirm_queue:
        self.confirm_queue[conversation_id] = queue.Queue()
      self.current_message[conversation_id] = message
      if self.on_confirmation_requested is not None:
        self.on_confirmation_requested(conversation_id, message)
      conversation_queue = self.confirm_queue[conversation_id]
    return conversation_queue.get()

  def provide_confirmation(self, conversation_id: ConversationId,
                           confirmation: str) -> None:
    with self.message_lock:
      if conversation_id not in self.confirm_queue:
        self.confirm_queue[conversation_id] = queue.Queue()
      conversation_queue = self.confirm_queue[conversation_id]
      self.current_message.pop(conversation_id, None)
    conversation_queue.put(confirmation)

  def get_pending_message(self,
                          conversation_id: ConversationId) -> Optional[str]:
    with self.message_lock:
      return self.current_message.get(conversation_id)


class ConfirmationState:
  """Manages confirmations and interaction limits using the confirmation manager."""

  def __init__(self,
               confirmation_manager: ConfirmationManager,
               confirm_every: Optional[int] = None) -> None:
    self.confirmation_manager: ConfirmationManager = confirmation_manager
    self.confirm_every: Optional[int] = confirm_every
    self.interaction_count: int = 0

  def RegisterInteraction(self, conversation_id: ConversationId) -> None:
    """Registers an interaction and potentially requires a confirmation."""
    if self.confirm_every is not None:
      self.interaction_count += 1
      if self.interaction_count >= self.confirm_every:
        self.RequireConfirmation(
            conversation_id,
            "Confirm operations after N interactions? Enter guidance or an empty string to continue: "
        )
        self.interaction_count = 0

  def RequireConfirmation(self, conversation_id: ConversationId,
                          message: str) -> Optional[str]:
    """Requires explicit confirmation through the confirmation manager."""
    return self.confirmation_manager.RequireConfirmation(
        conversation_id, message)
