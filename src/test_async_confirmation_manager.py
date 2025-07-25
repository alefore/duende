import unittest
import threading
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

  def provide_confirmation(self, message) -> None:
    self.manager.provide_confirmation(self.conversation_id, message)

  def test_provide_confirmation(self) -> None:
    """Test providing confirmation."""
    confirmation_thread = threading.Thread(
        target=self.provide_confirmation, args=("Yes",))
    confirmation_thread.start()

    test_message = "Are you sure?"
    confirmation = self.manager.RequireConfirmation(self.conversation_id,
                                                    test_message)

    self.assertEqual(confirmation, "Yes",
                     "Confirmation should match the provided input.")
    confirmation_thread.join()

  def test_pending_message(self) -> None:
    """Test that a message is pending until confirmation is given."""
    test_message = "Confirm this action."
    pending_message_before = self.manager.get_pending_message(
        self.conversation_id)
    self.assertIsNone(pending_message_before,
                      "Pending message should initially be None.")

    # Start thread to set the confirmation
    confirmation_thread = threading.Thread(
        target=self.provide_confirmation, args=("Proceed",))
    confirmation_thread.start()

    # Message should be set before confirmation is provided
    pending_message = self.manager.RequireConfirmation(0, test_message)

    self.assertEqual(pending_message, "Proceed",
                     "Confirmation should be 'Proceed'.")
    confirmation_thread.join()


if __name__ == '__main__':
  unittest.main()
