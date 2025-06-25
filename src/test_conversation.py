import unittest
import os
import json
from conversation import Conversation, ConversationFactory, Message, MultilineContent, ContentSection


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

  def test_deserialize(self) -> None:
    new_format_data = {
        'role':
            'assistant',
        'content_sections': [{
            'content': ["New section A"],
            'summary': 'Summary A'
        }, {
            'content': ["New section B"],
            'summary': None
        }]
    }
    message = Message.Deserialize(new_format_data)
    self.assertEqual(message.role, "assistant")
    sections = message.GetContentSections()
    self.assertEqual(len(sections), 2)
    self.assertEqual(sections[0].content, ["New section A"])
    self.assertEqual(sections[0].summary, "Summary A")
    self.assertEqual(sections[1].content, ["New section B"])
    self.assertIsNone(sections[1].summary)

  def test_serialize(self) -> None:
    message = Message(
        role="user",
        content_sections=[
            ContentSection(content=["Hello"], summary="Greeting"),
            ContentSection(content=["World"])
        ])
    serialized_data = message.Serialize()
    expected_data = {
        'role':
            'user',
        'content_sections': [{
            'content': ["Hello"],
            'summary': "Greeting"
        }, {
            'content': ["World"]
        }]
    }
    self.assertEqual(serialized_data, expected_data)


if __name__ == '__main__':
  unittest.main()
