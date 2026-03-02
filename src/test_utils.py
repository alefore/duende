import asyncio

from file_access_policy import FileAccessPolicy
from confirmation import ConfirmationManager, ConfirmationState
from conversation import ConversationId, ConversationFactoryOptions
from selection_manager import SelectionManager


class FakeFileAccessPolicy(FileAccessPolicy):

  def allow_access(self, path: str) -> bool:
    return True  # Allow all access for testing


class FakeConfirmationState(ConfirmationState):

  async def RequireConfirmation(self, conversation_id: int,
                                prompt: str) -> str | None:
    return None  # Always confirm


class FakeConfirmationManager(ConfirmationManager):

  async def RequireConfirmation(self, conversation_id: ConversationId,
                                message: str) -> str | None:
    return None  # Always confirm for tests

  def provide_confirmation(self, conversation_id: ConversationId,
                           confirmation: str) -> None:
    pass


class FakeSelectionManager(SelectionManager):
  pass  # Default implementation is fine for now


def slow_conversation_factory_options() -> ConversationFactoryOptions:

  async def sleep(_: ConversationId) -> None:
    await asyncio.sleep(0.1)

  return ConversationFactoryOptions(on_message_added_callback=sleep)
