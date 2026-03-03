import aiofiles
import asyncio
import dataclasses
import json
import pathlib
import sqlite3
from typing import NewType
import uuid

from agent_loop_options import BaseAgentLoop
from agent_workflow import AgentWorkflow, AgentWorkflowFactory
from agent_workflow_options import AgentWorkflowOptions
from command_registry import CommandRegistry
from confirmation import ConfirmationManager, ConfirmationState
from conversation import ConversationId, Conversation
from done_command import DoneCommand
from list_files_command import ListFilesCommand
from message import ContentSection, Message
import message_bus
from message_bus import Message as BusMessage, MessageBus, SessionId, mark_message_as_seen, open_bus, wait_for_new_messages
from swarm_types import AgentName
from search_file_command import SearchFileCommand
from read_file_command import ReadFileCommand
from write_file_command import WriteFileCommand


@dataclasses.dataclass(frozen=True)
class AgentIdentityConfig:
  # Unique name of this agent
  name: AgentName

  capability: list[str]

  prompt_path: pathlib.Path


@dataclasses.dataclass(frozen=True)
class SwarmConfig:
  agents: dict[AgentName, AgentIdentityConfig]
  # Path to the SQLite DB containing the messages queue.
  messages_bus_path: pathlib.Path


class SwarmConfirmationManager(ConfirmationManager):

  def __init__(self, message_bus: MessageBus, agent_name: AgentName,
               session_id: SessionId, delegate: ConfirmationManager) -> None:
    self._message_bus = message_bus
    self._agent_name = agent_name
    self._session_id = session_id
    self._delegate = delegate

  async def RequireConfirmation(self, conversation_id: ConversationId,
                                message: str) -> str | None:
    dummy_id = message_bus.MessageId(0)
    await message_bus.write_new_message(
        self._message_bus,
        BusMessage(
            id=dummy_id,
            sender=self._agent_name,
            recipient=None,
            session_id=self._session_id,
            body=message))
    return await self._delegate.RequireConfirmation(conversation_id, message)

  def provide_confirmation(self, conversation_id: ConversationId,
                           confirmation: str) -> None:
    return self._delegate.provide_confirmation(conversation_id, confirmation)


@dataclasses.dataclass
class AgentSession:
  session_id: SessionId
  conversation: Conversation
  loop: BaseAgentLoop
  confirmation_manager: ConfirmationManager


class SwarmWorkflow(AgentWorkflow):

  def __init__(self, options: AgentWorkflowOptions) -> None:
    self._options = options
    self._background_tasks: list[asyncio.Task[None]] = []

  async def run(self) -> None:
    assert self._options.config_path
    self._config = await self._load_config(self._options.config_path)
    self._messages_bus = await open_bus(self._config.messages_bus_path)
    self._sessions: dict[SessionId, AgentSession] = {}
    while True:
      for message in await wait_for_new_messages(self._messages_bus,
                                                 list(self._config.agents)):
        await self._process_message(message)

  async def _load_config(self, path: pathlib.Path) -> SwarmConfig:
    """Loads the configuration from JSON file in `path`."""
    raise NotImplementedError()  # {{🍄 load config}}

  async def _process_message(self, message: BusMessage) -> None:
    """Marks the message as seen and processes it.

    If the message has a session_id, handles it to _provide_confirmation;
    otherwise, calls _start_new_session and updates _sessions.
    """
    raise NotImplementedError()  # {{🍄 process message}}

  async def _provide_confirmation(self, message) -> None:
    """Calls `provide_confirmation` on the session for the message.

    {{🦔 The value of `message.body` is passed to the right confirmation
         manager.}}
    """
    assert message.session_id
    assert message.session_id in self._sessions
    raise NotImplementedError()  # {{🍄 provide confirmation}}

  async def _start_new_session(self, message: BusMessage) -> AgentSession:
    """Starts a new session and registers it in self._sessions."""
    assert message.recipient
    session_id = SessionId(uuid.uuid4().hex)
    command_registry = self._create_command_registry(
        self._config.agents[message.recipient])
    conversation = self._options.conversation_factory.New(
        f"{message.recipient}: {message.body[:50]}", command_registry)
    confirmation_manager = SwarmConfirmationManager(
        self._messages_bus, message.recipient, session_id, self._options
        .agent_loop_options.confirmation_state.confirmation_manager)
    agent_loop_options = self._options.agent_loop_options._replace(
        conversation=conversation,
        start_message=await self._new_start_message(message),
        command_registry=command_registry,
        confirmation_state=ConfirmationState(confirmation_manager, 30))
    agent_loop = self._options.agent_loop_factory.new(agent_loop_options)
    # Update _background_tasks (from agent_loop.run()) and return AgentSession:
    raise NotImplementedError()  # {{🍄 register new session}}

  async def _new_start_message(self, message: BusMessage) -> Message:
    """Returns a new Message: agent's prompt + message's body.

    Loads the prompt from the agent's config's prompt_path and appends the body
    of the message to it.
    """
    assert message.recipient
    head_path = self._config.agents[message.recipient].prompt_path
    tail = "<user_request>" + message.body + "</user_request>"
    raise NotImplementedError()  # {{🍄 new start message}}

  def _create_command_registry(self,
                               config: AgentIdentityConfig) -> CommandRegistry:
    """Iterates over all config.capabilities."""
    registry = CommandRegistry()
    file_access_policy = self._options.agent_loop_options.file_access_policy
    registry.Register(ReadFileCommand(file_access_policy))
    registry.Register(ListFilesCommand(file_access_policy))
    registry.Register(SearchFileCommand(file_access_policy))
    registry.Register(DoneCommand(arguments=[]))
    return registry


class SwarmWorkflowFactory(AgentWorkflowFactory):

  def name(self) -> str:
    return "swarm"

  async def new(self, agent_workflow_options: AgentWorkflowOptions,
                args: dict[str, str]) -> AgentWorkflow:
    return SwarmWorkflow(agent_workflow_options)
