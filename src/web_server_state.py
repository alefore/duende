from typing import Optional
import logging
from flask_socketio import SocketIO, emit
from threading import Thread

from args_common import CreateAgentLoopOptions
from agent_loop import AgentLoop
from confirmation import AsyncConfirmationManager


class WebServerState:

  def __init__(self, args, socketio: SocketIO):
    self.socketio = socketio
    self.messages_sent = 0
    self.confirmation_manager = AsyncConfirmationManager(
        self._confirmation_requested)

    try:
      options = CreateAgentLoopOptions(args, self.confirmation_manager)
    except RuntimeError as e:
      logging.error(e)
      raise e

    self.agent_loop = AgentLoop(options)
    Thread(target=self.agent_loop.run).start()

  def SendUpdate(self, confirmation_required: Optional[bool]) -> None:
    new_messages = self.agent_loop.options.messages[self.messages_sent:]
    logging.info(
        f"Sending: From {self.messages_sent}, count: {len(new_messages)}.")
    if confirmation_required is None:
      confirmation_required = (
          self.confirmation_manager.get_pending_message() is not None)
    data = {
        'confirmation_required': confirmation_required,
        'conversation': new_messages
    }
    self.messages_sent += len(new_messages)
    self.socketio.emit('update', data)

  def _confirmation_requested(self, message_ignored: str) -> None:
    logging.info("Confirmation requested.")
    self.SendUpdate(True)

  def ReceiveConfirmation(self, confirmation_message) -> None:
    logging.info("Received confirmation.")
    self.confirmation_manager.provide_confirmation(confirmation_message)
