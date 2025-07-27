from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Dict, Optional
import asyncio
import logging
from dataclasses import dataclass

from conversation import ConversationId


@dataclass
class ConfirmationEntry:
  future: asyncio.Future[str]
  message: str


class ConfirmationManager(ABC):

  @abstractmethod
  async def RequireConfirmation(self, conversation_id: ConversationId,
                                message: str) -> Optional[str]:
    """Blocks execution until confirmation is given, returning additional guidance if provided by the user."""
    pass


class AsyncConfirmationManager(ConfirmationManager):

  def __init__(
      self,
      on_confirmation_requested: Optional[Callable[[ConversationId, str],
                                                   Coroutine[Any, Any,
                                                             None]]] = None
  ) -> None:
    self.confirmations: Dict[ConversationId, ConfirmationEntry] = {}
    self.on_confirmation_requested = on_confirmation_requested
    self._lock = asyncio.Lock()

  async def RequireConfirmation(self, conversation_id: ConversationId,
                                message: str) -> Optional[str]:
    async with self._lock:
      if conversation_id in self.confirmations:
        logging.fatal(
            f"RequireConfirmation called for conversation_id "
            f"{conversation_id} but a confirmation is already pending.")
        raise RuntimeError(
            f"Duplicate RequireConfirmation for {conversation_id}")

      future = asyncio.Future[str]()
      self.confirmations[conversation_id] = ConfirmationEntry(future, message)
    if self.on_confirmation_requested is not None:
      await self.on_confirmation_requested(conversation_id, message)
    return await future

  def provide_confirmation(self, conversation_id: ConversationId,
                           confirmation: str) -> None:

    async def _set_result() -> None:
      async with self._lock:
        entry = self.confirmations.pop(conversation_id, None)
        if entry and not entry.future.done():
          entry.future.set_result(confirmation)

    asyncio.create_task(_set_result())

  def get_pending_message(self,
                          conversation_id: ConversationId) -> Optional[str]:
    entry = self.confirmations.get(conversation_id)
    return entry.message if entry else None


class ConfirmationState:
  """Manages confirmations and interaction limits using the confirmation manager."""

  def __init__(self,
               confirmation_manager: ConfirmationManager,
               confirm_every: Optional[int] = None) -> None:
    self.confirmation_manager: ConfirmationManager = confirmation_manager
    self.confirm_every: Optional[int] = confirm_every
    self.interaction_count: int = 0

  async def RegisterInteraction(self, conversation_id: ConversationId) -> None:
    """Registers an interaction and potentially requires a confirmation."""
    if self.confirm_every is not None:
      self.interaction_count += 1
      if self.interaction_count >= self.confirm_every:
        await self.RequireConfirmation(
            conversation_id,
            "Confirm operations after N interactions? Enter guidance or an empty string to continue: "
        )
        self.interaction_count = 0

  async def RequireConfirmation(self, conversation_id: ConversationId,
                                message: str) -> Optional[str]:
    """Requires explicit confirmation through the confirmation manager."""
    return await self.confirmation_manager.RequireConfirmation(
        conversation_id, message)
