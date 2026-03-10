import asyncio
from concurrent.futures import ThreadPoolExecutor
import datetime
import dataclasses
import logging
import pathlib
import sqlite3
from typing import Callable, NewType, ParamSpec, TypeVar, cast

from conversation import ConversationId
from swarm_types import AgentName

# MessageId is meant for the IDs of messages in the SQL database. It is NOT
# meant for the IDs of Telegram messages (use TelegramMessageId for those).
MessageId = NewType("MessageId", int)  # Unique ID across the bus.
TelegramChatId = NewType("TelegramChatId", int)
TelegramMessageId = NewType("TelegramMessageId", int)

# Wrapper for the `content` fields in the message bus.
MessageContent = NewType("MessageContent", str)

# Fake agent name reserved to represent the end user.
END_USER_AGENT = AgentName("duende-internal:end-user")


@dataclasses.dataclass(frozen=True)
class Message:
  # The fields map directly to the rows of the `message_bus` SQL table.
  #
  # Paths use `pathlib.Path`.
  pass  # {{🍄 message fields}}


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
                                      lambda: func(*args, **kwargs))

  async def _poll_in_thread(self,
                            func: Callable[[], list[Message]]) -> list[Message]:
    """Runs `func` once per second until it returns values."""
    raise NotImplementedError()  # {{🍄 poll in thread}}

  async def open(self) -> None:
    """Connects to the bus, potentially initializing it.

    If the database is empty (or does not exist), creates the expected tables
    (see message_bus.sql for details).

    Passes timeout=20.0 and isolation_level=None when connecting.
    """

    def _open() -> None:
      raise NotImplementedError()  # {{🍄 init db}}

    await self._run_in_thread(_open)

  async def wait_for_incoming_messages(
      self, agents: list[AgentName]) -> list[Message]:
    """Polls until new incoming messages arrive for the agents listed.

    A new incoming message is one with `processed_at` set to NULL.
    """

    def _load_messages() -> list[Message]:
      """May return empty list."""
      raise NotImplementedError()  # {{🍄 load incoming messages}}

    return await self._poll_in_thread(_load_messages)

  async def wait_for_outgoing_messages(self) -> list[Message]:
    """Polls until new outgoing messages arrive.

    A new outgoing message is one with `telegram_message_id` set to `NULL` and
    `agent` set to the value in `END_USER_AGENT`.
    """

    def _load_messages() -> list[Message]:
      raise NotImplementedError()  # {{🍄 load outgoing messages}}

    return await self._poll_in_thread(_load_messages)

  async def set_conversation_id(self, message_id: MessageId,
                                conversation_id: ConversationId) -> None:
    raise NotImplementedError()  # {{🍄 set message conversation}}

  async def write_new_message(self, message: Message) -> Message:
    """Adds a new message to the database.

    The MessageId will be overwritten (based on database state) and the
    resulting message returned.
    """
    raise NotImplementedError()  # {{🍄 write new message}}

  async def mark_as_processed(self, message_id: MessageId) -> None:
    """Sets processed_at to the current time."""
    raise NotImplementedError()  # {{🍄 set processed at}}

  async def set_telegram_message_id(
      self, message_id: MessageId,
      telegram_message_id: TelegramMessageId) -> None:
    """Updates the telegram_message_id of a given row.

    It is an error to try to update a message_id where the telegram_message_id
    already has a value (we use a conditional update and validate that exactly
    1 row was updated).
    """
    raise NotImplementedError()  # {{🍄 set telegram message id}}

  async def read_message(self, message_id: MessageId) -> Message:
    """Returns a message from the database or raises ValueError."""
    raise NotImplementedError()  # {{🍄 read message}}

  async def find_message_by_telegram_id(
      self, telegram_chat_id: TelegramChatId,
      telegram_message_id: TelegramMessageId) -> Message:
    """Returns a message from the database or raises ValueError."""
    raise NotImplementedError()  # {{🍄 find message by telegram id}}
