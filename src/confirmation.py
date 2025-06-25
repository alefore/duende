from abc import ABC, abstractmethod
from typing import Optional, Callable
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
    self.confirm_queue: queue.Queue[str] = queue.Queue()
    self.message_lock = threading.Lock()
    self.current_message: Optional[str] = None
    self.on_confirmation_requested = on_confirmation_requested

  def RequireConfirmation(self, conversation_id: ConversationId,
                          message: str) -> Optional[str]:
    with self.message_lock:
      self.current_message = message
      if self.on_confirmation_requested is not None:
        self.on_confirmation_requested(conversation_id, message)
    confirmation = self.confirm_queue.get()  # Blocks until item is present
    with self.message_lock:
      self.current_message = None
    return confirmation

  def provide_confirmation(self, confirmation: str):
    self.confirm_queue.put(confirmation)

  def get_pending_message(self) -> Optional[str]:
    with self.message_lock:
      return self.current_message


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
