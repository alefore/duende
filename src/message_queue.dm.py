import asyncio


class AgentMessageQueue:

  def __init__(self) -> None:
    self._lock = asyncio.Lock()  # Guards access to _data.
    # The class can be in any of two states:
    #
    # * Somebody is waiting for messages: In this case, self._data is set to a
    #   future to be notified when the first message arrives.
    #
    # * Nobody is waiting for messages: In this case, self._data is set to a
    #   list, where messages will be collected.
    #
    # Calls to `read` may not happen concurrently.
    self._data: list[str] | asyncio.Future[list[str]] = []

  async def push(self, message: str) -> None:
    """Appends a message to the queue."""
    raise NotImplementedError()  # {{🍄 push}}

  async def read(self) -> list[str]:
    """Returns a non-empty list of messages (possibly blocking)."""
    raise NotImplementedError()  # {{🍄 read}}
