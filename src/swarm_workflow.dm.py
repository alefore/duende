import aiofiles
import asyncio
import dataclasses
import datetime
import json
import logging
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
from file_access_policy import create_file_access_policy, FileAccessPolicyConfig
from list_files_command import ListFilesCommand
from message import ContentSection, Message
import message_bus
from message_bus import Message as BusMessage, MessageBus, TelegramChatId, TelegramMessageId
from message_queue import AgentMessageQueue
from pathbox import PathBox
from shell_command_command import ShellCommandCommand
from swarm_commands import AskUserCommand, DelegateRequestConfig, DelegateRequestCommand, DisplayInfoCommand, PublishMessageCommand, PublishMessageConfig
from swarm_config import AgentIdentityConfig, SwarmConfig, load_config
from swarm_types import AgentName
from search_file_command import SearchFileCommand
from read_file_command import ReadFileCommand
from working_directory_command import ChangeWorkingDirectoryCommand
from write_file_command import WriteFileCommand


class SwarmConfirmationManager(ConfirmationManager):

  def __init__(self, message_bus: MessageBus, agent_name: AgentName,
               delegate: ConfirmationManager) -> None:
    self._message_bus = message_bus
    self._agent_name = agent_name
    self._delegate = delegate

  async def RequireConfirmation(self, conversation_id: ConversationId,
                                message: str) -> str | None:
    dummy_id = message_bus.MessageId(0)
    # TODO: Implement here.
    return await self._delegate.RequireConfirmation(conversation_id, message)

  def provide_confirmation(self, conversation_id: ConversationId,
                           confirmation: str) -> None:
    return self._delegate.provide_confirmation(conversation_id, confirmation)


@dataclasses.dataclass
class AgentSession:
  conversation: Conversation
  loop: BaseAgentLoop
  message_queue: AgentMessageQueue


class SwarmWorkflow(AgentWorkflow):

  def __init__(self, options: AgentWorkflowOptions) -> None:
    self._options = options
    self._background_tasks: list[asyncio.Task[None]] = []
    self._sessions: dict[ConversationId, AgentSession] = {}

  async def run(self) -> None:
    self._config = await load_config(
        self._options.config_path or pathlib.Path('swarm/config.json'))
    self._message_bus = MessageBus(self._config.message_bus_path)
    await self._message_bus.open()
    while True:
      for message in await self._message_bus.wait_for_incoming_messages(
          list(self._config.agents)):
        await self._process_message(message)

  async def _process_message(self, message: BusMessage) -> None:
    """Receives a new incoming message.

    Sets the `process_at` cell to the current time.

    * If `message.source_agent` is NOT the value in END_USER_AGENT: calls
      `_start_agent_loop`.

    * Otherwise, if the `message.message_reply_to_id is None`: calls
      `_start_agent_loop`.

    * Otherwise, if the replied-to message can be found in the bus and the
      replied-to message has a `conversation_id` found in `_sessions`: adds the
      content of the message to the session's `message_queue`.

    * Otherwise: writes an outgoing message informing the user that the session
      no longer exists.
    """
    raise NotImplementedError()  # {{🍄 process message}}

  async def _start_agent_loop(self, message: BusMessage) -> None:
    """Starts a new agent loop.

    Calls `MessageBus.set_conversation_id` to write the new conversation id.

    {{🦔 The agent loop is run with an exception handler that will *immediately*
         log any exceptions that it raises.
    """
    assert message.target_agent
    telegram_id = message.telegram_message_id or message.telegram_reply_to_id
    assert telegram_id
    agent_message_queue = AgentMessageQueue()
    command_registry = CommandRegistry()
    conversation = self._options.conversation_factory.New(
        f"{message.target_agent}: {message.content[:50]}", command_registry)
    self._init_command_registry(conversation.GetId(), telegram_id, message,
                                self._config.agents[message.target_agent],
                                agent_message_queue, command_registry)
    confirmation_manager = SwarmConfirmationManager(
        self._message_bus, message.target_agent, self._options
        .agent_loop_options.confirmation_state.confirmation_manager)
    agent_loop_options = self._options.agent_loop_options._replace(
        conversation=conversation,
        start_message=await self._new_start_message(message),
        command_registry=command_registry,
        file_access_policy=create_file_access_policy(self._config.agents[
            message.target_agent].command_registry.file_access_policy or
                                                     FileAccessPolicyConfig()),
        confirmation_state=ConfirmationState(confirmation_manager, 30))
    raise NotImplementedError()  # {{🍄 create and start agent loop}}

  async def _new_start_message(self, message: BusMessage) -> Message:
    """Returns a new Message: agent's prompt + message's body.

    Loads the prompt from the agent's config's prompt_path and appends the body
    of the message to it.
    """
    assert message.target_agent
    head = self._config.agents[message.target_agent].prompt_content
    tail = "<user_request>" + message.content + "</user_request>"
    raise NotImplementedError()  # {{🍄 new start message}}

  def _init_command_registry(self, conversation_id: ConversationId,
                             telegram_reply_to_id: TelegramMessageId,
                             message: BusMessage, config: AgentIdentityConfig,
                             queue: AgentMessageQueue,
                             command_registry: CommandRegistry) -> None:
    """Initializes a valid registry for a specific agent identity.

    {{🦔 The registry contains ReadFileCommand, ListFilesCommand,
         SearchFileCommand, DoneCommand (with no arguments),
         ChangeWorkingDirectoryCommand, DisplayInfoCommand and AskUserCommand.}}
    {{🦔 If `config.command_registry.allow_shell', the registry contains
         `ShellCommandCommand`.}}
    {{🦔 If `config.command_registry.delegate_request.allow_list' exists and
         is non-empty, the registry contains DelegateRequestCommand.}}
    {{🦔 If `config.command_registry.publish_message.allow_list' exists and
         is non-empty, the registry contains PublishMessageCommand.}}
    {{🦔 If `config.command_registry.writes', the registry contains
         `WriteFileCommand`.}}
    {{🦔 If `message.local_directory` is None, the cwd passed to relevant
         agent commands comes from self._options.}}
    {{🦔 If `message.local_directory` is not None, the cwd passed to relevant
         agent commands is:
         self._options.agent_loop_options.cwd / message.local_directory.}}
    {{🦔 The file access policy is based on config.file_access_policy_regex.}}
    """
    # TODO: Figure out how to honor
    # config.command_registry.writes.file_access_policy. With the current
    # implementation of WriteFileCommand, it isn't feasible.

    raise NotImplementedError()  # {{🍄 init command registry}}


class SwarmWorkflowFactory(AgentWorkflowFactory):

  def name(self) -> str:
    return "swarm"

  async def new(self, agent_workflow_options: AgentWorkflowOptions,
                args: dict[str, str]) -> AgentWorkflow:
    return SwarmWorkflow(agent_workflow_options)
