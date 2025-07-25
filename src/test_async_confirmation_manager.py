import unittest
import asyncio
from confirmation import AsyncConfirmationManager


class TestAsyncConfirmationManager(unittest.TestCase):

  def setUp(self) -> None:
    self.manager = AsyncConfirmationManager()
    self.conversation_id = 0

  def test_initial_state(self) -> None:
    """Test the initial state of AsyncConfirmationManager."""
    self.assertIsNone(
        self.manager.get_pending_message(self.conversation_id),
        "Initial message should be None.")

  async def provide_confirmation(self, message) -> None:
    self.manager.provide_confirmation(self.conversation_id, message)

  async def test_provide_confirmation(self) -> None:
    """Test providing confirmation."""
    confirmation_task = asyncio.create_task(self.provide_confirmation("Yes"))
    await asyncio.sleep(0.01) # Give the task a chance to run

    test_message = "Are you sure?"
    confirmation = await self.manager.RequireConfirmation(self.conversation_id,
                                                    test_message)

    self.assertEqual(confirmation, "Yes",
                     "Confirmation should match the provided input.")
    await confirmation_task

  async def test_pending_message(self) -> None:
    """Test that a message is pending until confirmation is given."""
    test_message = "Confirm this action."
    pending_message_before = self.manager.get_pending_message(
        self.conversation_id)
    self.assertIsNone(pending_message_before,
                      "Pending message should initially be None.")

    # Start task to set the confirmation
    confirmation_task = asyncio.create_task(self.provide_confirmation("Proceed"))
    await asyncio.sleep(0.01) # Give the task a chance to run

    # Message should be set before confirmation is provided
    pending_message = await self.manager.RequireConfirmation(0, test_message)

    self.assertEqual(pending_message, "Proceed",
                     "Confirmation should be 'Proceed'.")
    await confirmation_task


if __name__ == '__main__':
  unittest.main()
