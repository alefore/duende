import unittest
from conversation import Message, MultilineContent, ContentSection


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

  def test_serialize(self):
    message = Message(
        role="user",
        content_sections=[
            ContentSection(content=["Hello, world!"], summary="Section 1"),
            ContentSection(content=["Second line."])
        ])
    expected = {
        'role':
            'user',
        'content_sections': [{
            'content': ["Hello, world!"],
            'summary': "Section 1"
        }, {
            'content': ["Second line."]
        }]
    }
    self.assertEqual(message.Serialize(), expected)

  def test_deserialize(self):
    data = {
        'role':
            'user',
        'content_sections': [{
            'content': ["Hello, world!"],
            'summary': "Intro"
        }, {
            'content': ["Second line."]
        }]
    }
    message = Message.Deserialize(data)
    self.assertEqual(message.role, "user")
    sections = message.GetContentSections()
    self.assertEqual(len(sections), 2)
    self.assertEqual(sections[0].content, ["Hello, world!"])
    self.assertEqual(sections[0].summary, "Intro")
    self.assertEqual(sections[1].content, ["Second line."])
    self.assertIsNone(sections[1].summary)

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
