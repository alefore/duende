from typing import Any, Callable, Coroutine, Dict, List, NamedTuple, Optional
import json
import logging
import threading
from datetime import datetime, timezone
import aiofiles
import asyncio

from conversation_state import ConversationState
from agent_command import CommandInput, CommandOutput
from message import Message, ContentSection
from command_registry import CommandRegistry

ConversationId = int


class ConversationFactoryOptions(NamedTuple):
  on_message_added_callback: Optional[Callable[[ConversationId],
                                               Coroutine[Any, Any,
                                                         None]]] = None
  on_state_changed_callback: Optional[Callable[[ConversationId],
                                               Coroutine[Any, Any,
                                                         None]]] = None
  command_registry: Optional[CommandRegistry] = None


class Conversation:

  def __init__(
      self,
      unique_id: int,
      name: str,
      path: Optional[str],
      command_registry: CommandRegistry,
      on_message_added_callback: Optional[Callable[[int],
                                                   Coroutine[Any, Any,
                                                             None]]] = None,
      on_state_changed_callback: Optional[Callable[[ConversationId],
                                                   Coroutine[Any, Any,
                                                             None]]] = None
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

  @classmethod
  async def create(
      cls,
      unique_id: int,
      name: str,
      path: Optional[str],
      command_registry: CommandRegistry,
      on_message_added_callback: Optional[Callable[[int],
                                                   Coroutine[Any, Any,
                                                             None]]] = None,
      on_state_changed_callback: Optional[Callable[[ConversationId],
                                                   Coroutine[Any, Any,
                                                             None]]] = None
  ) -> "Conversation":
    self = cls(unique_id, name, path, command_registry,
               on_message_added_callback, on_state_changed_callback)
    if self.path is not None:
      try:
        async with aiofiles.open(self.path, 'r') as f:
          self.messages.extend(
              Message.Deserialize(message_data)
              for message_data in json.loads(await f.read()))
      except (FileNotFoundError, json.JSONDecodeError, KeyError):
        logging.info("Invalid or missing data. Starting new conversation.")
    return self

  async def _Save(self) -> None:
    if self.path is not None:
      async with aiofiles.open(self.path, 'w') as f:
        await f.write(
            json.dumps([message.Serialize() for message in self.messages],
                       indent=2))

  async def _derive_args(self, message: Message) -> Message:
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
                      derived_args=await
                      command.derive_args(section.command.args)),
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

  async def AddMessage(self, message: Message) -> None:
    message = await self._derive_args(message)
    logging.info(self._DebugString(message))
    self.messages.append(message)
    await self._Save()
    if self._on_message_added_callback:
      await self._on_message_added_callback(self._unique_id)

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

  async def SetState(self, state: ConversationState) -> None:
    if self._state == state:
      return
    self._state = state
    self.last_state_change_time = datetime.now(timezone.utc)
    if self._on_state_changed_callback:
      await self._on_state_changed_callback(self._unique_id)


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

  async def New(self, name: str, path: Optional[str]) -> Conversation:
    with self._lock:
      reserved_id = self._next_id
      self._next_id += 1
    output = await Conversation.create(reserved_id, name, path,
                                       self._command_registry,
                                       self.on_message_added_callback,
                                       self.on_state_changed_callback)
    self._conversations[reserved_id] = output
    return output

  def Get(self, id: ConversationId) -> Conversation:
    return self._conversations[id]

  def GetAll(self) -> List[Conversation]:
    return list(self._conversations.values())
