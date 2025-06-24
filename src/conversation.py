from typing import List, Dict, Any, Optional, Callable
import json
import logging

MultilineContent = List[str]


class Message:

  def __init__(self,
               role: str,
               content_sections: Optional[List[MultilineContent]] = None):
    self.role = role
    self._content_sections: List[MultilineContent] = content_sections if content_sections is not None else []

  def Serialize(self) -> Dict[str, Any]:
    return {'role': self.role, 'content_sections': self._content_sections}

  @staticmethod
  def Deserialize(data: Dict[str, Any]) -> 'Message':
    message = Message(role=data['role'])
    message._content_sections = data.get('content_sections', [])
    return message

  def GetContentListStr(self) -> List[str]:
    combined_content: List[str] = []
    for section in self._content_sections:
      combined_content.extend(section)
    return combined_content

  def GetContentSections(self) -> List[MultilineContent]:
    return self._content_sections

  def PushSection(self, section: MultilineContent) -> None:
    self._content_sections.append(section)


class Conversation:

  def __init__(
      self,
      on_message_added_callback: Optional[Callable[[], None]] = None) -> None:
    self.messages: List[Message] = []
    self._on_message_added_callback = on_message_added_callback

  @staticmethod
  def Load(
      path: str,
      on_message_added_callback: Optional[Callable[[], None]] = None
  ) -> 'Conversation':
    conversation = Conversation(on_message_added_callback)
    try:
      with open(path, 'r') as f:
        messages_data = json.load(f)
        conversation.messages.extend(
            Message.Deserialize(message_data) for message_data in messages_data)
    except (FileNotFoundError, json.JSONDecodeError):
      logging.info("Invalid or missing data. Starting new conversation.")
    return conversation

  def Save(self, path: str) -> None:
    with open(path, 'w') as f:
      json.dump([message.Serialize() for message in self.messages], f, indent=2)

  def AddMessage(self, message: Message) -> None:
    logging.info(f"Add message: {message.role}: {message.GetContentListStr()}")
    self.messages.append(message)
    if self._on_message_added_callback:
      self._on_message_added_callback()

  def GetMessagesList(self) -> List[Message]:
    return self.messages
