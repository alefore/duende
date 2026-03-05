import asyncio
from concurrent.futures import ThreadPoolExecutor
import dataclasses
from functools import partial
import logging
import pathlib
import sqlite3
from typing import Callable, NewType, ParamSpec, TypeVar

from swarm_types import AgentName

SenderName = AgentName | None
RecipientName = AgentName | None
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


T = TypeVar("T")
P = ParamSpec("P")


class MessageBus:

  def __init__(self, path: pathlib.Path) -> None:
    self._path = path
    self._executor = ThreadPoolExecutor(max_workers=1)
    # _connection is only accessed by threads running in _executor.
    self._connection: sqlite3.Connection | None = None

  async def _run_in_thread(self, func: Callable[P, T], *args: P.args,
                           **kwargs: P.kwargs) -> T:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(self._executor,
                                      partial(func, *args, **kwargs))

  async def open(self) -> None:
    """Connects to the bus, potentially initializing it.

    If the database is empty (or does not exist), creates the expected tables
    (see message_bus.sql for details).

    Passes timeout=20.0 and isolation_level=None when connecting.
    """

    def _open() -> sqlite3.Connection:
      raise NotImplementedError()  # {{🍄 init db}}

    await self._run_in_thread(_open)

  async def wait_for_new_messages(
      self, recipients: list[RecipientName]) -> list[Message]:
    """Polls db until new messages arrive for the recipients listed.

    A new message is one with status set to 'new'.

    Initially polls after one second, growing polling frequency exponentially up
    to one minute.

    Calls logging.info as it polls/sleeps.
    """

    def _load_messages() -> list[Message]:
      """May return empty list."""
      raise NotImplementedError()  # {{🍄 load messages}}

    # Call _load_messages (with exponential back-off) in _executor until it returns messages:
    raise NotImplementedError()  # {{🍄 poll for new messages}}

  async def mark_message_as_seen(self, message_id: MessageId) -> None:
    """Updates the `status` field in self._messages_db to `seen`."""
    raise NotImplementedError()  # {{🍄 mark message as seen}}

  async def write_new_message(self, message: Message) -> MessageId:
    """Adds a new message to the database.

    The MessageId will be overwritten (based on database state) and returned.
    """
    raise NotImplementedError()  # {{🍄 write new message}}
