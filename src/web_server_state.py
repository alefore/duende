from typing import List, Optional
import logging
from flask_socketio import SocketIO
from threading import Thread

from args_common import CreateAgentLoopOptions
from agent_loop import AgentLoop
from confirmation import AsyncConfirmationManager
from random_key import GenerateRandomKey
from conversation import Message


class WebServerState:

  def __init__(self, args, socketio: SocketIO):
    self.socketio = socketio
    self.confirmation_manager = AsyncConfirmationManager(
        self._confirmation_requested)
    self.session_key = GenerateRandomKey()

    try:
      options = CreateAgentLoopOptions(
          args,
          self.confirmation_manager,
          on_message_added_callback=lambda: self.SendUpdate(
              None, confirmation_required=None))
    except RuntimeError as e:
      logging.error(e)
      raise e

    self.agent_loop = AgentLoop(options)
    Thread(target=self.agent_loop.run).start()

  def SendUpdate(self, client_message_count: Optional[int],
                 confirmation_required: Optional[bool]) -> None:
    if client_message_count is not None:
      new_messages = self._GetMessagesList()[client_message_count:]
      logging.info(
          f"Client has {client_message_count} messages. "
          f"Sending from {client_message_count}, count: {len(new_messages)}.")
    else:
      new_messages = []
      logging.info("Sending update without new messages.")

    if confirmation_required is None:
      confirmation_required = (
          self.confirmation_manager.get_pending_message() is not None)
    data = {
        'confirmation_required': confirmation_required,
        'conversation': [m.Serialize() for m in new_messages],
        'message_count': len(self._GetMessagesList()),
        'session_key': self.session_key,
        'first_message_index': client_message_count or 0
    }
    self.socketio.emit('update', data)

  def _GetMessagesList(self) -> List[Message]:
    return self.agent_loop.conversation.GetMessagesList()

  def _confirmation_requested(self, message_ignored: str) -> None:
    logging.info("Confirmation requested.")
    self.SendUpdate(None, confirmation_required=True)

  def ReceiveConfirmation(self, confirmation_message) -> None:
    logging.info("Received confirmation.")
    self.confirmation_manager.provide_confirmation(confirmation_message)
