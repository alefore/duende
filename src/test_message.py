import unittest
from conversation import Message, MultilineContent, ContentSection
from datetime import datetime, timezone


class TestMessage(unittest.TestCase):

  def test_initialization(self):
    message = Message(
        role="user",
        content_sections=[
            ContentSection(content=["Hello, world!"], summary=None)
        ])
    self.assertEqual(message.role, "user")
    self.assertEqual(message.GetContentSections()[0].content, ["Hello, world!"])
    self.assertIsNone(message.GetContentSections()[0].summary)

  def test_initialization_with_summary(self):
    message = Message(
        role="user",
        content_sections=[
            ContentSection(content=["Hello, world!"], summary="A greeting")
        ])
    self.assertEqual(message.role, "user")
    self.assertEqual(message.GetContentSections()[0].content, ["Hello, world!"])
    self.assertEqual(message.GetContentSections()[0].summary, "A greeting")

  def test_initialization_empty_content(self):
    message = Message(role="system")
    self.assertEqual(message.role, "system")
    self.assertEqual(message.GetContentSections(), [])

  def test_deserialize(self) -> None:
    now = datetime.now(timezone.utc)
    format_data = {
        'role': 'assistant',
        'content_sections': [{
            'content': ["New section A"],
            'summary': 'Summary A'
        }, {
            'content': ["New section B"],
            'summary': None
        }],
        'creation_time': now.isoformat(),
    }
    message = Message.Deserialize(format_data)
    self.assertEqual(message.role, "assistant")
    self.assertEqual(message.creation_time, now)
    sections = message.GetContentSections()
    self.assertEqual(len(sections), 2)
    self.assertEqual(sections[0].content, ["New section A"])
    self.assertEqual(sections[0].summary, "Summary A")
    self.assertEqual(sections[1].content, ["New section B"])
    self.assertIsNone(sections[1].summary)

  def test_serialize(self) -> None:
    now = datetime.now(timezone.utc)
    message = Message(
        role="user",
        content_sections=[
            ContentSection(content=["Hello"], summary="Greeting"),
            ContentSection(content=["World"])
        ],
        creation_time=now)
    expected_data = {
        'role': 'user',
        'content_sections': [{
            'content': ["Hello"],
            'summary': "Greeting"
        }, {
            'content': ["World"]
        }],
        'creation_time': now.isoformat(),
    }
    self.assertEqual(message.Serialize(), expected_data)

  def test_get_content_sections(self):
    section1 = ContentSection(
        content=["First section line 1", "First section line 2"],
        summary="Section 1")
    section2 = ContentSection(content=["Second section line 1"], summary=None)
    message = Message(role="system", content_sections=[section1, section2])
    self.assertEqual(message.GetContentSections(), [section1, section2])

  def test_push_section(self):
    message = Message(role="user")
    self.assertEqual(message.GetContentSections(), [])

    section1 = ContentSection(content=["Part A"], summary=None)
    message.PushSection(section1)
    self.assertEqual(message.GetContentSections(), [section1])

    section2 = ContentSection(
        content=["Part B", "Part C"], summary="Summary for BC")
    message.PushSection(section2)
    self.assertEqual(message.GetContentSections(), [section1, section2])


if __name__ == '__main__':
  unittest.main()
