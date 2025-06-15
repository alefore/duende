from abc import ABC, abstractmethod
from typing import Optional, List, Dict
import threading
import queue


class ConfirmationManager(ABC):

  @abstractmethod
  def RequireConfirmation(self, message: str) -> Optional[str]:
    """Blocks execution until confirmation is given, returning additional guidance if provided by the user."""
    pass


class CLIConfirmationManager(ConfirmationManager):

  def RequireConfirmation(self, message: str) -> Optional[str]:
    print(message)
    return input(
        "Confirm operations? Enter a message to provide guidance to the AI: "
    ).strip()


class AsyncConfirmationManager(ConfirmationManager):

  def __init__(self):
    self.confirm_queue = queue.Queue()
    self.message_lock = threading.Lock()
    self.current_message: Optional[str] = None

  def RequireConfirmation(self, message: str) -> Optional[str]:
    with self.message_lock:
      self.current_message = message
    confirmation = self.confirm_queue.get()  # Blocks until item is present
    with self.message_lock:
      self.current_message = None
    return confirmation

  def provide_confirmation(self, confirmation: str):
    self.confirm_queue.put(confirmation)

  def get_pending_message(self) -> Optional[str]:
    with self.message_lock:
      return self.current_message
