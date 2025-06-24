import unittest
from conversation import Message, MultilineContent


class TestMessage(unittest.TestCase):

  def test_initialization(self):
    message = Message(role="user", content_sections=[["Hello, world!"]])
    self.assertEqual(message.role, "user")
    self.assertEqual(message.GetContentListStr(), ["Hello, world!"])
    self.assertEqual(message.GetContentSections(), [["Hello, world!"]])

  def test_initialization_empty_content(self):
    message = Message(role="system")
    self.assertEqual(message.role, "system")
    self.assertEqual(message.GetContentListStr(), [])
    self.assertEqual(message.GetContentSections(), [])

  def test_serialize(self):
    message = Message(
        role="user", content_sections=[["Hello, world!"], ["Second line."]])
    expected = {
        'role': 'user',
        'content_sections': [["Hello, world!"], ["Second line."]]
    }
    self.assertEqual(message.Serialize(), expected)

  def test_deserialize(self):
    data = {
        'role': 'user',
        'content_sections': [["Hello, world!"], ["Second line."]]
    }
    message = Message.Deserialize(data)
    self.assertEqual(message.role, "user")
    self.assertEqual(message.GetContentListStr(),
                     ["Hello, world!", "Second line."])
    self.assertEqual(message.GetContentSections(),
                     [["Hello, world!"], ["Second line."]])

  def test_get_content_list_str(self):
    message = Message(
        role="assistant", content_sections=[["Line 1"], ["Line 2", "Line 3"]])
    self.assertEqual(message.GetContentListStr(),
                     ["Line 1", "Line 2", "Line 3"])

  def test_get_content_sections(self):
    section1: MultilineContent = [
        "First section line 1", "First section line 2"
    ]
    section2: MultilineContent = ["Second section line 1"]
    message = Message(role="system", content_sections=[section1, section2])
    self.assertEqual(message.GetContentSections(), [section1, section2])

  def test_push_section(self):
    message = Message(role="user")
    self.assertEqual(message.GetContentSections(), [])

    section1: MultilineContent = ["Part A"]
    message.PushSection(section1)
    self.assertEqual(message.GetContentSections(), [section1])
    self.assertEqual(message.GetContentListStr(), ["Part A"])

    section2: MultilineContent = ["Part B", "Part C"]
    message.PushSection(section2)
    self.assertEqual(message.GetContentSections(), [section1, section2])
    self.assertEqual(message.GetContentListStr(),
                     ["Part A", "Part B", "Part C"])


if __name__ == '__main__':
  unittest.main()
