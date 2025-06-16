import unittest
import threading
from confirmation import AsyncConfirmationManager


class TestAsyncConfirmationManager(unittest.TestCase):

  def setUp(self):
    self.manager = AsyncConfirmationManager()

  def test_initial_state(self):
    """Test the initial state of AsyncConfirmationManager."""
    self.assertIsNone(self.manager.get_pending_message(),
                      "Initial message should be None.")

  def provide_confirmation(self, message):
    self.manager.provide_confirmation(message)

  def test_provide_confirmation(self):
    """Test providing confirmation."""
    confirmation_thread = threading.Thread(
        target=self.provide_confirmation, args=("Yes",))
    confirmation_thread.start()

    test_message = "Are you sure?"
    confirmation = self.manager.RequireConfirmation(test_message)

    self.assertEqual(confirmation, "Yes",
                     "Confirmation should match the provided input.")
    confirmation_thread.join()

  def test_pending_message(self):
    """Test that a message is pending until confirmation is given."""
    test_message = "Confirm this action."
    pending_message_before = self.manager.get_pending_message()
    self.assertIsNone(pending_message_before,
                      "Pending message should initially be None.")

    # Start thread to set the confirmation
    confirmation_thread = threading.Thread(
        target=self.provide_confirmation, args=("Proceed",))
    confirmation_thread.start()

    # Message should be set before confirmation is provided
    pending_message = self.manager.RequireConfirmation(test_message)

    self.assertEqual(pending_message, "Proceed",
                     "Confirmation should be 'Proceed'.")
    confirmation_thread.join()


if __name__ == '__main__':
  unittest.main()
