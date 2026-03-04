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
class SwarmTelegramConfig:
  token: str

  consumer_agent: AgentName

  end_user_identity: AgentName

  authorized_users: list[TelegramId]


@dataclasses.dataclass(frozen=True)
class SwarmConfig:
  agents: dict[AgentName, AgentIdentityConfig]
  # Path to the SQLite DB containing the messages queue.
  message_bus_path: pathlib.Path

  telegram: SwarmTelegramConfig | None


async def load_config(path: pathlib.Path) -> SwarmConfig:
  """Loads the configuration from JSON file in `path`.

  If `telegram` is present, `telegram.token` MUST be set.
  If `telegram.token` is set:

  * `telegram.authorized_users` MUST NOT be empty.
  * `telegram.consumer_agent` MUST be set to a key in `agents`.
  * `telegram.end_user_identity` MUST NOT be a key in `agents`.
  """
  raise NotImplementedError()  # {{🍄 load config}}
