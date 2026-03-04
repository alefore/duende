import aiofiles
import dataclasses
import json
import pathlib
from typing import NewType

TelegramId = NewType("TelegramId", int)

from swarm_types import AgentName


@dataclasses.dataclass(frozen=True)
class AgentIdentityConfig:
  # Unique name of this agent
  name: AgentName

  capability: list[str]

  prompt_path: pathlib.Path

  file_access_policy_regex: str


@dataclasses.dataclass(frozen=True)
class SwarmConfig:
  agents: dict[AgentName, AgentIdentityConfig]
  # Path to the SQLite DB containing the messages queue.
  message_bus_path: pathlib.Path

  telegram_token: str | None

  telegram_consumer: AgentName | None

  telegram_authorized_users: list[TelegramId]


async def load_config(path: pathlib.Path) -> SwarmConfig:
  """Loads the configuration from JSON file in `path`.

  If `telegram_token` is set:

  * `telegram_authorized_users` must not be empty.
  * `telegram_consumer` must be set to a key in `agents`.

  If `telegram_authorized_users` or `telegram_consumer` is set, `telegram_token`
  must also be set.
  """
  raise NotImplementedError()  # {{🍄 load config}}
