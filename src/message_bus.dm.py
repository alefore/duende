import asyncio
import dataclasses
import logging
import pathlib
import sqlite3
from typing import NewType

from swarm_types import AgentName

SenderName = AgentName | None
RecipientName = AgentName | None
MessageBus = NewType('MessageBus', sqlite3.Connection)
MessageId = NewType('MessageId', int)  # Unique ID across the bus.
SessionId = NewType('SessionId', str)  # A UUID.


@dataclasses.dataclass(frozen=True)
class Message:
  # Fields for the rows in the `message_bus` table (see message_bus.sql).
  id: MessageId
  sender: SenderName
  recipient: RecipientName
  session_id: SessionId | None
  body: str


async def open_bus(path: pathlib.Path) -> MessageBus:
  """Connects to the bus, potentially initializing it.

  If the database is empty (or does not exist), creates the expected tables
  (see message_bus.sql for details).

  Passes timeout=20.0 and isolation_level=None when connecting.
  """
  raise NotImplementedError()  # {{🍄 open bus}}


async def wait_for_new_messages(
    db: MessageBus, recipients: list[RecipientName]) -> list[Message]:
  """Polls db until new messages arrive for the recipients listed.

  A new message is one with status set to 'new'.

  Initially polls after one second, growing polling frequency exponentially up
  to one minute.

  Calls logging.info as it polls/sleeps.
  """
  raise NotImplementedError()  # {{🍄 wait for new messages}}


async def mark_message_as_seen(db: MessageBus, message_id: MessageId) -> None:
  """Updates the `status` field in self._messages_db to `seen`."""
  raise NotImplementedError()  # {{🍄 mark message as seen}}


async def write_new_message(db: MessageBus, message: Message) -> MessageId:
  """Adds a new message to the database.

  The MessageId will be overwritten (based on database state) and returned.
  """
  raise NotImplementedError()  # {{🍄 write new message}}
