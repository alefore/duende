import unittest
from unittest.mock import MagicMock, patch
from agent_server import app, agent_loop_instance, confirmation_manager


class TestAgentServer(unittest.TestCase):

  def setUp(self):
    self.app = app.test_client()
    self.app.testing = True

    # Create and push an application context
    self.app_context = app.app_context()
    self.app_context.push()

    global agent_loop_instance, confirmation_manager
    # Mock agent_loop_instance and confirmation_manager
    agent_loop_instance = MagicMock()
    # Create a "real" list to test append behavior
    agent_loop_instance.options.messages = []
    confirmation_manager = MagicMock()

  def tearDown(self):
    self.app_context.pop()

  def test_interact_get(self):
    response = self.app.get('/')
    self.assertEqual(response.status_code, 200)
    self.assertIn(b"No conversation yet.", response.data)

  @patch('agent_server.agent_loop_instance')
  def test_interact_post(self, mock_agent_loop_instance):
    mock_agent_loop_instance.options.messages = []

    response = self.app.post(
        '/', data={'prompt': 'Test prompt'}, follow_redirects=True)
    self.assertEqual(response.status_code, 200)
    self.assertIn({
        'role': 'user',
        'content': 'Test prompt'
    }, mock_agent_loop_instance.options.messages)

  @patch('agent_server.confirmation_manager')
  def test_confirm_post(self, mock_confirmation_manager):
    # Mock pending message for confirmation
    mock_confirmation_manager.get_pending_message.return_value = "Please confirm something"

    response = self.app.get('/')
    self.assertIn(b"Please confirm something", response.data)

    response = self.app.post(
        '/confirm', data={'confirmation': 'Confirmed'}, follow_redirects=True)
    self.assertEqual(response.status_code, 200)
    mock_confirmation_manager.provide_confirmation.assert_called_once_with(
        'Confirmed')


if __name__ == '__main__':
  unittest.main()
