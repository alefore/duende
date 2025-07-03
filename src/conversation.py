from typing import List, Dict, Any, Optional, Callable, NamedTuple
import json
import logging
from datetime import datetime, timezone

from conversation_state import ConversationState
from agent_command import CommandInput, CommandOutput


class ContentSection(NamedTuple):
  content: str
  command: Optional[CommandInput] = None
  command_output: Optional[CommandOutput] = None
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
      if section.command is not None:
        section_dict['command'] = str(section.command)
      if section.command_output is not None:
        section_dict['command_output'] = str(section.command_output)
      serialized_sections.append(section_dict)
    return {
        'role': self.role,
        'content_sections': serialized_sections,
        'creation_time': self.creation_time.isoformat()
    }

  def ToPropertiesDict(self) -> Dict[str, Any]:
    serialized_sections = []
    for section in self._content_sections:
      section_dict: Dict[str, Any] = {'content': section.content}
      if section.summary is not None:
        section_dict['summary'] = section.summary
      if section.command is not None:
        command_dict = {
            'command_name': section.command.command_name,
        }
        for key, value in section.command.args.items():
            command_dict[key] = str(value)
        section_dict['command'] = command_dict
      if section.command_output is not None:
        section_dict['command_output'] = {
            'command_name': section.command_output.command_name,
            'output': str(section.command_output.output),
            'errors': str(section.command_output.errors),
            'summary': str(section.command_output.summary),
            'task_done': str(section.command_output.task_done)
        }
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
              content="".join(section_data.get('content', [])),
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
      path: str,
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
    self.last_state_change_time: datetime = datetime.now(timezone.utc)
    self.path = path
    try:
      with open(path, 'r') as f:
        self.messages.extend(
            Message.Deserialize(message_data) for message_data in json.load(f))
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
      logging.info("Invalid or missing data. Starting new conversation.")

  def _Save(self) -> None:
    with open(self.path, 'w') as f:
      json.dump([message.Serialize() for message in self.messages], f, indent=2)

  def AddMessage(self, message: Message) -> None:
    logging.info(self._DebugString(message))
    self.messages.append(message)
    self._Save()
    if self._on_message_added_callback:
      self._on_message_added_callback(self._unique_id)

  def _DebugString(self, message: Message) -> str:
    content_sections: List[ContentSection] = message.GetContentSections()
    content: str = ""
    for section in content_sections:
      content += section.content
    return (f"Add message: {message.role}: {len(content_sections)} sections: "
            f"{content[:50]}...")

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
    self.last_state_change_time = datetime.now(timezone.utc)
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

  def New(self, name: str, path: str) -> Conversation:
    output = Conversation(self._next_id, name, path,
                          self.on_message_added_callback,
                          self.on_state_changed_callback)
    self._conversations[self._next_id] = output
    self._next_id += 1
    return output

  def Get(self, id: ConversationId) -> Conversation:
    return self._conversations[id]

  def GetAll(self) -> List[Conversation]:
    return list(self._conversations.values())
