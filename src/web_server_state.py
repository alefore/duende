from typing import List, Optional
import logging
from flask_socketio import SocketIO
from threading import Thread

from args_common import CreateAgentLoopOptions
from agent_loop import AgentLoop
from confirmation import AsyncConfirmationManager
from random_key import GenerateRandomKey
from conversation import ConversationFactory, ConversationId, Message


class WebServerState:

  def __init__(self, args, socketio: SocketIO) -> None:
    self.socketio = socketio
    self.confirmation_manager = AsyncConfirmationManager(
        self._confirmation_requested)
    self.session_key = GenerateRandomKey()

    self.conversation_factory = ConversationFactory(
        lambda id: self.SendUpdate(id, None, confirmation_required=None))
    try:
      options = CreateAgentLoopOptions(args, self.confirmation_manager,
                                       self.conversation_factory)
    except RuntimeError as e:
      logging.error(e)
      raise e

    Thread(target=AgentLoop(options).run).start()

  def SendUpdate(self, conversation_id, client_message_count: Optional[int],
                 confirmation_required: Optional[str]) -> None:
    try:
      conversation = self.conversation_factory.Get(conversation_id)
      conversation_name = conversation.GetName()
      messages_list = conversation.GetMessagesList()
    except KeyError:
      logging.error(
          f"Conversation with ID {conversation_id} not found. Cannot send update."
      )
      return

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
    data = {
        'conversation_id': conversation_id,
        'conversation_name': conversation_name,
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

  def ReceiveConfirmation(self, confirmation_message) -> None:
    logging.info("Received confirmation.")
    self.confirmation_manager.provide_confirmation(confirmation_message)
