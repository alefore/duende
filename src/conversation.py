from typing import List, Dict, Any, Optional, Callable, NamedTuple
import json
import logging
import threading
from datetime import datetime, timezone

from conversation_state import ConversationState
from agent_command import CommandInput, CommandOutput
from message import Message, ContentSection
from command_registry import CommandRegistry

ConversationId = int


class ConversationFactoryOptions(NamedTuple):
  on_message_added_callback: Optional[Callable[[ConversationId], None]] = None
  on_state_changed_callback: Optional[Callable[[ConversationId], None]] = None
  command_registry: Optional[CommandRegistry] = None


class Conversation:

  def __init__(
      self,
      unique_id: int,
      name: str,
      path: str,
      command_registry: CommandRegistry,
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
    self._command_registry = command_registry
    try:
      with open(path, 'r') as f:
        self.messages.extend(
            Message.Deserialize(message_data) for message_data in json.load(f))
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
      logging.info("Invalid or missing data. Starting new conversation.")

  def _Save(self) -> None:
    with open(self.path, 'w') as f:
      json.dump([message.Serialize() for message in self.messages], f, indent=2)

  def _derive_args(self, message: Message) -> Message:
    # Iterate over content sections and compute derived args for commands
    output_content_sections: List[ContentSection] = []
    for section in message.GetContentSections():
      if section.command:
        command_name = section.command.command_name
        command = self._command_registry.Get(command_name)
        if command:
          output_content_sections.append(
              ContentSection(
                  content=section.content,
                  command=CommandInput(
                      command_name=section.command.command_name,
                      args=section.command.args,
                      derived_args=command.derive_args(section.command.args)),
                  command_output=section.command_output,
                  summary=section.summary))
        else:
          output_content_sections.append(section)
      else:
        output_content_sections.append(section)

    return Message(
        role=message.role,
        content_sections=output_content_sections,
        creation_time=message.creation_time)

  def AddMessage(self, message: Message) -> None:
    message = self._derive_args(message)
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

  def __init__(self, options: ConversationFactoryOptions) -> None:
    self._lock = threading.Lock()
    self._next_id: ConversationId = 0
    self._conversations: Dict[ConversationId, Conversation] = {}
    self.on_message_added_callback = options.on_message_added_callback
    self.on_state_changed_callback = options.on_state_changed_callback
    if options.command_registry is None:
      raise ValueError(
          "CommandRegistry must be set on ConversationFactoryOptions.")
    self._command_registry: CommandRegistry = options.command_registry

  def New(self, name: str, path: str) -> Conversation:
    with self._lock:
      reserved_id = self._next_id
      self._next_id += 1
    output = Conversation(reserved_id, name, path, self._command_registry,
                          self.on_message_added_callback,
                          self.on_state_changed_callback)
    self._conversations[reserved_id] = output
    return output

  def Get(self, id: ConversationId) -> Conversation:
    return self._conversations[id]

  def GetAll(self) -> List[Conversation]:
    return list(self._conversations.values())
