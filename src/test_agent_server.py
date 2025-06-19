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
    self.assertIn(b"<div id=\"conversation\"></div>", response.data)
    self.assertIn(b"<div id=\"confirmation\"></div>", response.data)


if __name__ == '__main__':
  unittest.main()
