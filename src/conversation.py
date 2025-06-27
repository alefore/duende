from typing import List, Dict, Any, Optional, Callable, NamedTuple
import json
import logging
from datetime import datetime, timezone
from conversation_state import ConversationState

# Avoid strings with newline characters; to break lines, just add more entries.
MultilineContent = List[str]


class ContentSection(NamedTuple):
  content: MultilineContent
  summary: Optional[str] = None


class Message:

  def __init__(self,
               role: str,
               content_sections: Optional[List[ContentSection]] = None,
               creation_time: Optional[datetime] = None):
    self.role = role
    self._content_sections: List[
        ContentSection] = content_sections if content_sections is not None else []
    self.creation_time = creation_time or datetime.now(timezone.utc)

  def Serialize(self) -> Dict[str, Any]:
    serialized_sections = []
    for section in self._content_sections:
      section_dict: Dict[str, Any] = {'content': section.content}
      if section.summary is not None:
        section_dict['summary'] = section.summary
      serialized_sections.append(section_dict)
    return {
        'role': self.role,
        'content_sections': serialized_sections,
        'creation_time': self.creation_time.isoformat()
    }

  @staticmethod
  def Deserialize(data: Dict[str, Any]) -> 'Message':
    content_sections: List[ContentSection] = []
    raw_sections = data.get('content_sections', [])
    for section_data in raw_sections:
      content_sections.append(
          ContentSection(
              content=section_data.get('content', []),
              summary=section_data.get('summary')))
    return Message(
        role=data['role'],
        content_sections=content_sections,
        creation_time=datetime.fromisoformat(data['creation_time']))

  def GetContentSections(self) -> List[ContentSection]:
    return self._content_sections

  def PushSection(self, section: ContentSection) -> None:
    self._content_sections.append(section)


ConversationId = int


class Conversation:

  def __init__(
      self,
      unique_id: int,
      name: str,
      on_message_added_callback: Optional[Callable[[int], None]] = None,
      on_state_changed_callback: Optional[Callable[[ConversationId],
                                                   None]] = None
  ) -> None:
    self._unique_id = unique_id
    self._name = name
    self.messages: List[Message] = []
    self._on_message_added_callback = on_message_added_callback
    self._on_state_changed_callback = on_state_changed_callback
    self._state: ConversationState = ConversationState.STARTING

  @staticmethod
  def Load(
      unique_id: int,
      path: str,
      name: str,
      on_message_added_callback: Optional[Callable[[ConversationId],
                                                   None]] = None,
      on_state_changed_callback: Optional[Callable[[ConversationId],
                                                   None]] = None
  ) -> 'Conversation':
    conversation = Conversation(unique_id, name, on_message_added_callback,
                                on_state_changed_callback)
    try:
      with open(path, 'r') as f:
        conversation.messages.extend(
            Message.Deserialize(message_data) for message_data in json.load(f))
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
      logging.info("Invalid or missing data. Starting new conversation.")
    return conversation

  def Save(self, path: str) -> None:
    with open(path, 'w') as f:
      json.dump([message.Serialize() for message in self.messages], f, indent=2)

  def AddMessage(self, message: Message) -> None:
    content_sections = message.GetContentSections()
    num_sections = len(content_sections)
    first_section_content_log = "''"
    if content_sections:
      content_list = content_sections[0].content
      if content_list:
        first_section_content_log = f"'{content_list[0][:50]}...'"
    logging.info(
        f"Add message: {message.role}: {num_sections} sections, first: {first_section_content_log}"
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

  def GetState(self) -> ConversationState:
    return self._state

  def SetState(self, state: ConversationState) -> None:
    if self._state == state:
      return
    self._state = state
    if self._on_state_changed_callback:
      self._on_state_changed_callback(self._unique_id)


class ConversationFactory:

  def __init__(
      self,
      on_message_added_callback: Optional[Callable[[ConversationId],
                                                   None]] = None,
      on_state_changed_callback: Optional[Callable[[ConversationId],
                                                   None]] = None
  ) -> None:
    self._next_id: ConversationId = 0
    self._conversations: Dict[ConversationId, Conversation] = {}
    self.on_message_added_callback = on_message_added_callback
    self.on_state_changed_callback = on_state_changed_callback

  def New(self, name: str) -> Conversation:
    output = Conversation(self._next_id, name, self.on_message_added_callback,
                          self.on_state_changed_callback)
    self._conversations[self._next_id] = output
    self._next_id += 1
    return output

  def Load(self, path: str, name: str) -> Conversation:
    output = Conversation.Load(self._next_id, path, name,
                               self.on_message_added_callback,
                               self.on_state_changed_callback)
    self._conversations[self._next_id] = output
    self._next_id += 1
    return output

  def Get(self, id: ConversationId) -> Conversation:
    return self._conversations[id]

  def GetAll(self) -> List[Conversation]:
    return list(self._conversations.values())
