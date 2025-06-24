import unittest
import os
import json
from conversation import Conversation, Message, MultilineContent


class TestConversation(unittest.TestCase):

  def setUp(self):
    self.test_file = 'test_conversation.json'
    self.conversation = Conversation()

  def tearDown(self):
    if os.path.exists(self.test_file):
      os.remove(self.test_file)

  def test_initialization(self):
    self.assertEqual(len(self.conversation.messages), 0)

  def test_add_message(self):
    message = Message(role="user", content_sections=[["Hello, world!"]])
    self.conversation.AddMessage(message)
    self.assertEqual(len(self.conversation.messages), 1)
    self.assertEqual(self.conversation.messages[0].GetContentSections(),
                     [["Hello, world!"]])

  def test_get_messages_list(self):
    message = Message(role="user", content_sections=[["Hello, world!"]])
    self.conversation.AddMessage(message)
    messages = self.conversation.GetMessagesList()
    self.assertEqual(len(messages), 1)
    self.assertEqual(messages[0].GetContentSections(), [["Hello, world!"]])

  def test_save_and_load(self):
    message = Message(role="user", content_sections=[["Hello, world!"]])
    self.conversation.AddMessage(message)
    self.conversation.Save(self.test_file)

    loaded_conversation = Conversation.Load(self.test_file)
    loaded_messages = loaded_conversation.GetMessagesList()
    self.assertEqual(len(loaded_messages), 1)
    self.assertEqual(loaded_messages[0].GetContentSections(),
                     [["Hello, world!"]])

  def test_load_nonexistent_file(self):
    loaded_conversation = Conversation.Load("nonexistent_file.json")
    self.assertEqual(len(loaded_conversation.messages), 0)

  def test_load_invalid_json(self):
    with open(self.test_file, 'w') as f:
      f.write("Invalid JSON")

    loaded_conversation = Conversation.Load(self.test_file)
    self.assertEqual(len(loaded_conversation.messages), 0)


if __name__ == '__main__':
  unittest.main()
