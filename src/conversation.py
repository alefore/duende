from typing import List, Dict, Any, Optional, Callable
import json
import logging
from datetime import datetime, timezone

from conversation_state import ConversationState
from agent_command import CommandInput, CommandOutput
from message import Message, ContentSection

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
