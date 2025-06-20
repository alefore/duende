from typing import List, Dict, Any
import json
import logging


class Message:

  def __init__(self, role: str, content: str):
    self.role = role
    self.content = content

  def Serialize(self) -> Dict[str, str]:
    return {'role': self.role, 'content': self.content}

  @staticmethod
  def Deserialize(data: Dict[str, Any]) -> 'Message':
    return Message(role=data['role'], content=data['content'])


class Conversation:

  def __init__(self) -> None:
    self.messages: List[Message] = []

  @staticmethod
  def Load(path: str) -> 'Conversation':
    conversation = Conversation()
    try:
      with open(path, 'r') as f:
        messages = json.load(f)
        conversation.messages.extend(
            Message.Deserialize(message) for message in messages)
    except (FileNotFoundError, json.JSONDecodeError):
      logging.info("Invalid or missing data. Starting new conversation.")
    return conversation

  def Save(self, path: str) -> None:
    with open(path, 'w') as f:
      json.dump([message.Serialize() for message in self.messages], f, indent=2)

  def AddMessage(self, message: Message) -> None:
    self.messages.append(message)

  def GetMessagesList(self) -> List[Message]:
    return self.messages
