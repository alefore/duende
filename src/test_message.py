import unittest
from conversation import Message

class TestMessage(unittest.TestCase):

    def test_initialization(self):
        message = Message(role="user", content="Hello, world!")
        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hello, world!")

    def test_serialize(self):
        message = Message(role="user", content="Hello, world!")
        expected = {'role': 'user', 'content': 'Hello, world!'}
        self.assertEqual(message.Serialize(), expected)

    def test_deserialize(self):
        data = {'role': 'user', 'content': 'Hello, world!'}
        message = Message.Deserialize(data)
        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hello, world!")


if __name__ == '__main__':
    unittest.main()