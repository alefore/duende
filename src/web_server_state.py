import asyncio
import argparse
import logging
from pydantic import BaseModel
from typing import Any
import socketio

from args_common import CreateAgentWorkflowOptions
from agent_loop import AgentLoop
from agent_loop_options import AgentLoopOptions
from agent_workflow import AgentWorkflow
from agent_workflow_options import AgentWorkflowOptions
from confirmation import AsyncConfirmationManager
from conversation import Conversation, ConversationFactory, ConversationId, ConversationFactoryOptions
from implement_workflow import ImplementAndReviewWorkflow
from message import Message
from principle_review_workflow import PrincipleReviewWorkflow
from random_key import GenerateRandomKey
from review_evaluator_test_workflow import ReviewEvaluatorTestWorkflow
from workflow_registry import StandardWorkflowFactoryContainer


class CreateAgentWorkflowData(BaseModel):
  name: str
  args: dict[str, str]


class WebServerState:

  def __init__(self, socketio: socketio.AsyncServer) -> None:
    self.socketio = socketio
    self.session_key = GenerateRandomKey()
    self._background_tasks: list[asyncio.Task[None]] = []
    self._workflow_factory_container = StandardWorkflowFactoryContainer()
    self._conversation_factory = ConversationFactory(
        ConversationFactoryOptions(
            on_message_added_callback=self._on_conversation_updated,
            on_state_changed_callback=self._on_conversation_updated))

  async def start(self, args: argparse.Namespace) -> None:
    self.confirmation_manager = AsyncConfirmationManager(
        self._confirmation_requested)
    try:
      self._agent_workflow_options: AgentWorkflowOptions = await CreateAgentWorkflowOptions(
          args, self.confirmation_manager, self._conversation_factory)
    except RuntimeError as e:
      logging.error(e)
      raise e

    logging.info(str(self._agent_workflow_options))
    agent_workflow: AgentWorkflow | None = None

    if args.workflow:
      factory = self._workflow_factory_container.get(args.workflow)
      if not factory:
        logging.error(f"Unknown workflow: {args.workflow}")
        raise ValueError(f"Unknown workflow: {args.workflow}")
      agent_workflow = await factory.new(self._agent_workflow_options, {})
    elif args.input:
      agent_workflow = PrincipleReviewWorkflow(self._agent_workflow_options)
    elif args.evaluate_evaluators:
      agent_workflow = ReviewEvaluatorTestWorkflow(self._agent_workflow_options)
    elif args.task:
      agent_workflow = ImplementAndReviewWorkflow(self._agent_workflow_options)
    if agent_workflow:
      self._background_tasks.append(asyncio.create_task(agent_workflow.run()))
    else:
      # Never shut down.
      self._background_tasks.append(
          asyncio.create_task(asyncio.sleep(float('inf'))))

  async def wait_for_background_tasks(self) -> None:
    while self._background_tasks:
      snapshot = list(self._background_tasks)
      logging.info(f"Waiting for tasks: ${len(snapshot)}")
      await asyncio.gather(*snapshot)
      self._background_tasks = [
          t for t in self._background_tasks if t not in snapshot
      ]

  async def _on_conversation_updated(self,
                                     conversation_id: ConversationId) -> None:
    logging.info(f"Conversation {conversation_id} updated.")
    await self.send_update(conversation_id, None, confirmation_required=None)

  async def send_update(self, conversation_id: ConversationId,
                        client_message_count: int | None,
                        confirmation_required: str | None) -> None:
    try:
      conversation = self._conversation_factory.Get(conversation_id)
    except KeyError:
      logging.error(
          f"Conversation with ID {conversation_id} not found. Cannot send update."
      )
      return

    messages_list = conversation.GetMessagesList()
    if client_message_count is not None:
      new_messages = messages_list[client_message_count:]
      logging.info(
          f"Client has {client_message_count} messages. "
          f"Sending from {client_message_count}, count: {len(new_messages)}.")
    else:
      new_messages = []
      logging.info("Sending update without new messages.")

    if confirmation_required is None:
      confirmation_required = self.confirmation_manager.get_pending_message(
          conversation_id)
    state = conversation.GetState()
    data = {
        'conversation_id':
            conversation_id,
        'conversation_name':
            conversation.GetName(),
        'conversation_state':
            state.name,
        'conversation_state_emoji':
            state.to_emoji(),
        'last_state_change_time':
            conversation.last_state_change_time.isoformat(),
        'confirmation_required':
            confirmation_required,
        'conversation': [m.ToPropertiesDict() for m in new_messages],
        'message_count':
            len(messages_list),
        'session_key':
            self.session_key,
        'first_message_index':
            client_message_count or 0
    }
    await self.socketio.emit('update', data)

  async def _confirmation_requested(self, conversation_id: ConversationId,
                                    message: str) -> None:
    logging.info("Confirmation requested.")
    await self.send_update(conversation_id, None, confirmation_required=message)

  def ReceiveConfirmation(self, confirmation_message: str,
                          conversation_id: int) -> None:
    logging.info("Received confirmation.")
    self.confirmation_manager.provide_confirmation(conversation_id,
                                                   confirmation_message)

  def _conversation_dict(self, conversation: Conversation) -> dict[str, Any]:
    state = conversation.GetState()
    return {
        'id':
            conversation.GetId(),
        'name':
            conversation.GetName(),
        'message_count':
            len(conversation.GetMessagesList()),
        'state':
            state.name,
        'state_emoji':
            state.to_emoji(),
        'last_state_change_time':
            conversation.last_state_change_time.isoformat()
    }

  async def list_conversations(self, start_id: int = 0) -> None:
    logging.info(f"Listing conversations with start_id={start_id}.")
    all_conversations = self._conversation_factory.GetAll()
    MAX_CONVERSATIONS_PER_UPDATE = 10
    await self.socketio.emit(
        'list_conversations', {
            'conversations':
                sorted((self._conversation_dict(c)
                        for c in all_conversations
                        if c.GetId() >= start_id),
                       key=lambda c: c['id'])[:MAX_CONVERSATIONS_PER_UPDATE],
            'max_conversation_id':
                max(c.GetId() for c in all_conversations)
        })

  async def list_workflow_factories(self) -> None:
    await self.socketio.emit(
        'list_workflow_factories',
        {'factories': sorted(self._workflow_factory_container.factory_names())})

  async def create_agent_workflow(self, data: CreateAgentWorkflowData) -> None:
    factory = self._workflow_factory_container.get(data.name)
    if not factory:
      logging.info(f"Unknown workflow factory: {data.name}")
      return
    logging.info(f"Create workflow: {data.name}")
    workflow = await factory.new(self._agent_workflow_options, data.args)
    self._background_tasks.append(asyncio.create_task(workflow.run()))


async def create_web_server_state(args: argparse.Namespace,
                                  sio: socketio.AsyncServer) -> WebServerState:
  output = WebServerState(sio)
  await output.start(args)
  return output
