from file_access_policy import FileAccessPolicy
from confirmation import ConfirmationManager, ConfirmationState
from conversation import ConversationId
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


class FakeSelectionManager(SelectionManager):
  pass  # Default implementation is fine for now
