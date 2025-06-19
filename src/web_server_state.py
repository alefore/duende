from typing import Optional
import logging
from flask_socketio import SocketIO
from threading import Thread

from args_common import CreateAgentLoopOptions
from agent_loop import AgentLoop
from confirmation import AsyncConfirmationManager
from random_key import GenerateRandomKey


class WebServerState:

  def __init__(self, args, socketio: SocketIO):
    self.socketio = socketio
    self.confirmation_manager = AsyncConfirmationManager(
        self._confirmation_requested)
    self.session_key = GenerateRandomKey()

    try:
      options = CreateAgentLoopOptions(args, self.confirmation_manager)
    except RuntimeError as e:
      logging.error(e)
      raise e

    self.agent_loop = AgentLoop(options)
    Thread(target=self.agent_loop.run).start()

  def SendUpdate(self, client_message_count: Optional[int],
                 confirmation_required: Optional[bool]) -> None:
    if client_message_count is not None:
      new_messages = self.agent_loop.options.messages[client_message_count:]
      logging.info(
          f"Client has {client_message_count} messages. Sending from {client_message_count}, count: {len(new_messages)}."
      )
    else:
      new_messages = []
      logging.info("Sending update without new messages.")

    if confirmation_required is None:
      confirmation_required = (
          self.confirmation_manager.get_pending_message() is not None)
    data = {
        'confirmation_required': confirmation_required,
        'conversation': new_messages,
        'message_count': len(self.agent_loop.options.messages),
        'session_key': self.session_key
    }
    self.socketio.emit('update', data)

  def _confirmation_requested(self, message_ignored: str) -> None:
    logging.info("Confirmation requested.")
    self.SendUpdate(None, confirmation_required=True)

  def ReceiveConfirmation(self, confirmation_message) -> None:
    logging.info("Received confirmation.")
    self.confirmation_manager.provide_confirmation(confirmation_message)
