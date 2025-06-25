from typing import List, Dict, Any, Optional, Callable
import json
import logging

# Avoid strings with newline characters; to break lines, just add more entries.
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

  def GetContentSections(self) -> List[MultilineContent]:
    return self._content_sections

  def PushSection(self, section: MultilineContent) -> None:
    self._content_sections.append(section)


ConversationId = int


class Conversation:

  def __init__(
      self,
      unique_id: int,
      name: str,
      on_message_added_callback: Optional[Callable[[int],
                                                   None]] = None) -> None:
    self._unique_id = unique_id
    self._name = name
    self.messages: List[Message] = []
    self._on_message_added_callback = on_message_added_callback

  @staticmethod
  def Load(
      unique_id: int,
      path: str,
      name: str,
      on_message_added_callback: Optional[Callable[[ConversationId],
                                                   None]] = None
  ) -> 'Conversation':
    conversation = Conversation(unique_id, name, on_message_added_callback)
    try:
      with open(path, 'r') as f:
        conversation.messages.extend(
            Message.Deserialize(message_data) for message_data in json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
      logging.info("Invalid or missing data. Starting new conversation.")
    return conversation

  def Save(self, path: str) -> None:
    with open(path, 'w') as f:
      json.dump([message.Serialize() for message in self.messages], f, indent=2)

  def AddMessage(self, message: Message) -> None:
    content_sections = message.GetContentSections()
    num_sections = len(content_sections)
    first_section_summary = f"'{content_sections[0][0][:50]}...'" if content_sections and content_sections[
        0] else "''"
    logging.info(
        f"Add message: {message.role}: {num_sections} sections, first: {first_section_summary}"
    )
    self.messages.append(message)
    if self._on_message_added_callback:
      self._on_message_added_callback(self._unique_id)

  def GetMessagesList(self) -> List[Message]:
    return self.messages

  def GetId(self) -> ConversationId:
    return self._unique_id

  def GetName(self) -> str:
    return self._name


class ConversationFactory:

  def __init__(
      self,
      on_message_added_callback: Optional[Callable[[ConversationId],
                                                   None]] = None
  ) -> None:
    self._next_id: ConversationId = 0
    self._conversations: Dict[ConversationId, Conversation] = {}
    self.on_message_added_callback = on_message_added_callback

  def New(self, name: str) -> Conversation:
    output = Conversation(self._next_id, name, self.on_message_added_callback)
    self._conversations[self._next_id] = output
    self._next_id += 1
    return output

  def Load(self, path: str, name: str) -> Conversation:
    output = Conversation.Load(self._next_id, path, name,
                               self.on_message_added_callback)
    self._conversations[self._next_id] = output
    self._next_id += 1
    return output

  def Get(self, id: ConversationId) -> Conversation:
    return self._conversations[id]
