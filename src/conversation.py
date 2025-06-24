from typing import List, Dict, Any, Optional, Callable
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

  def __init__(self, on_message_added_callback: Optional[Callable[[], None]] = None) -> None:
    self.messages: List[Message] = []
    self._on_message_added_callback = on_message_added_callback

  @staticmethod
  def Load(path: str, on_message_added_callback: Optional[Callable[[], None]] = None) -> 'Conversation':
    conversation = Conversation(on_message_added_callback)
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
    logging.info(f"Add message: {message}")
    self.messages.append(message)
    if self._on_message_added_callback:
      self._on_message_added_callback()

  def GetMessagesList(self) -> List[Message]:
    return self.messages
