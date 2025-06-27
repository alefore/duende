import unittest
import os
import json
from conversation import Conversation, ConversationFactory, Message, MultilineContent, ContentSection
from datetime import datetime, timezone


class TestConversation(unittest.TestCase):

  def setUp(self) -> None:
    self.test_file = 'test_conversation.json'
    self.conversation = ConversationFactory().New(name="Test Conversation")

  def tearDown(self) -> None:
    if os.path.exists(self.test_file):
      os.remove(self.test_file)

  def test_initialization(self) -> None:
    self.assertEqual(len(self.conversation.messages), 0)

  def test_add_message(self) -> None:
    message = Message(
        role="user",
        content_sections=[
            ContentSection(content=["Hello, world!"], summary=None)
        ])
    self.conversation.AddMessage(message)
    self.assertEqual(len(self.conversation.messages), 1)
    self.assertEqual(
        self.conversation.messages[0].GetContentSections()[0].content,
        ["Hello, world!"])
    self.assertIsNone(
        self.conversation.messages[0].GetContentSections()[0].summary)

  def test_get_messages_list(self) -> None:
    message = Message(
        role="user",
        content_sections=[
            ContentSection(content=["Hello, world!"], summary=None)
        ])
    self.conversation.AddMessage(message)
    messages = self.conversation.GetMessagesList()
    self.assertEqual(len(messages), 1)
    self.assertEqual(messages[0].GetContentSections()[0].content,
                     ["Hello, world!"])

  def test_save_and_load(self) -> None:
    message = Message(
        role="user",
        content_sections=[
            ContentSection(content=["Hello, world!"], summary="Greeting")
        ])
    self.conversation.AddMessage(message)
    self.conversation.Save(self.test_file)

    loaded_conversation = ConversationFactory().Load(
        self.test_file, name="Loaded Conversation")
    loaded_messages = loaded_conversation.GetMessagesList()
    self.assertEqual(len(loaded_messages), 1)
    self.assertEqual(loaded_messages[0].GetContentSections()[0].content,
                     ["Hello, world!"])
    self.assertEqual(loaded_messages[0].GetContentSections()[0].summary,
                     "Greeting")

  def test_load_nonexistent_file(self) -> None:
    loaded_conversation = ConversationFactory().Load(
        "nonexistent_file.json", name="Non-existent Conversation")
    self.assertEqual(len(loaded_conversation.messages), 0)

  def test_load_invalid_json(self) -> None:
    with open(self.test_file, 'w') as f:
      f.write("Invalid JSON")

    loaded_conversation = ConversationFactory().Load(
        self.test_file, name="Invalid JSON Conversation")
    self.assertEqual(len(loaded_conversation.messages), 0)


if __name__ == '__main__':
  unittest.main()
