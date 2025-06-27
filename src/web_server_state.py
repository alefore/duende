from typing import List, Optional
import argparse
import logging
from flask_socketio import SocketIO
from threading import Thread

from args_common import CreateAgentLoopOptions
from agent_loop import AgentLoop
from confirmation import AsyncConfirmationManager
from random_key import GenerateRandomKey
from conversation import ConversationFactory, ConversationId, Message


class WebServerState:

  def __init__(self, args: argparse.Namespace, socketio: SocketIO) -> None:
    self.socketio = socketio
    self.confirmation_manager = AsyncConfirmationManager(
        self._confirmation_requested)
    self.session_key = GenerateRandomKey()

    self.conversation_factory = ConversationFactory(
        on_message_added_callback=self._on_conversation_updated,
        on_state_changed_callback=self._on_conversation_updated)
    try:
      options = CreateAgentLoopOptions(args, self.confirmation_manager,
                                       self.conversation_factory)
    except RuntimeError as e:
      logging.error(e)
      raise e

    Thread(target=AgentLoop(options).run).start()

  def _on_conversation_updated(self, conversation_id: ConversationId) -> None:
    logging.info(f"Conversation {conversation_id} updated.")
    self.SendUpdate(conversation_id, None, confirmation_required=None)

  def SendUpdate(self, conversation_id: ConversationId,
                 client_message_count: Optional[int],
                 confirmation_required: Optional[str]) -> None:
    try:
      conversation = self.conversation_factory.Get(conversation_id)
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
      confirmation_required = self.confirmation_manager.get_pending_message()
    state = conversation.GetState()
    data = {
        'conversation_id': conversation_id,
        'conversation_name': conversation.GetName(),
        'conversation_state': f"{state.to_emoji()} {state.name}",
        'confirmation_required': confirmation_required,
        'conversation': [m.Serialize() for m in new_messages],
        'message_count': len(messages_list),
        'session_key': self.session_key,
        'first_message_index': client_message_count or 0
    }
    self.socketio.emit('update', data)

  def _confirmation_requested(self, conversation_id: ConversationId,
                              message: str) -> None:
    logging.info("Confirmation requested.")
    self.SendUpdate(conversation_id, None, confirmation_required=message)

  def ReceiveConfirmation(self, confirmation_message: str) -> None:
    logging.info("Received confirmation.")
    self.confirmation_manager.provide_confirmation(confirmation_message)

  def ListConversations(self) -> None:
    logging.info("Listing conversations.")
    conversations_data = []
    for conversation in self.conversation_factory.GetAll():
      state = conversation.GetState()
      conversations_data.append({
          'id': conversation.GetId(),
          'name': conversation.GetName(),
          'message_count': len(conversation.GetMessagesList()),
          'state': f"{state.to_emoji()} {state.name}",
      })
    self.socketio.emit('list_conversations', conversations_data)
