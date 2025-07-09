from typing import List, Optional
import argparse
import logging
from flask_socketio import SocketIO
from threading import Thread

from args_common import CreateAgentWorkflow
from agent_loop import AgentLoop
from agent_loop_options import AgentLoopOptions
from agent_workflow import AgentWorkflow
from confirmation import AsyncConfirmationManager
from random_key import GenerateRandomKey
from conversation import ConversationFactory, ConversationId, ConversationFactoryOptions
from message import Message


class WebServerState:

  def __init__(self, args: argparse.Namespace, socketio: SocketIO) -> None:
    self.socketio = socketio
    self.confirmation_manager = AsyncConfirmationManager(
        self._confirmation_requested)
    self.session_key = GenerateRandomKey()

    conversation_factory_options = ConversationFactoryOptions(
        on_message_added_callback=self._on_conversation_updated,
        on_state_changed_callback=self._on_conversation_updated)
    try:
      self.agent_workflow: AgentWorkflow = CreateAgentWorkflow(
          args, self.confirmation_manager, conversation_factory_options)
    except RuntimeError as e:
      logging.error(e)
      raise e

    Thread(target=self.agent_workflow.run).start()

  def _on_conversation_updated(self, conversation_id: ConversationId) -> None:
    logging.info(f"Conversation {conversation_id} updated.")
    self.SendUpdate(conversation_id, None, confirmation_required=None)

  def SendUpdate(self, conversation_id: ConversationId,
                 client_message_count: Optional[int],
                 confirmation_required: Optional[str]) -> None:
    try:
      conversation = self.agent_workflow.get_conversation_by_id(conversation_id)
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
    self.socketio.emit('update', data)

  def _confirmation_requested(self, conversation_id: ConversationId,
                              message: str) -> None:
    logging.info("Confirmation requested.")
    self.SendUpdate(conversation_id, None, confirmation_required=message)

  def ReceiveConfirmation(self, confirmation_message: str,
                          conversation_id: int) -> None:
    logging.info("Received confirmation.")
    self.confirmation_manager.provide_confirmation(conversation_id,
                                                   confirmation_message)

  def ListConversations(self) -> None:
    logging.info("Listing conversations.")
    conversations_data = []
    for conversation in self.agent_workflow.get_all_conversations():
      state = conversation.GetState()
      conversations_data.append({
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
      })
    self.socketio.emit('list_conversations', conversations_data)
