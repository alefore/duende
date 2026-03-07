import aiofiles
import dataclasses
import json
import pathlib
from typing import NewType

from command_registry_factory import create_command_registry_config, CommandRegistryConfig
from swarm_types import AgentName

TelegramId = NewType("TelegramId", int)


@dataclasses.dataclass(frozen=True)
class AgentIdentityConfig:
  # Unique name of this agent
  name: AgentName

  command_registry: CommandRegistryConfig

  promt_content: str


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


async def _load_agent_identity_config(
    path: pathlib.Path) -> AgentIdentityConfig:
  """Loads an AgentIdentityConfig for the agent at a given path (directory).

  `name` is the path's base-name.

  `command_registry` is loaded from a JSON file `config.json`. This file
  contains a directory with a `command_registry` key (in the future will contain
  other things).

  `prompt` is loaded (asynchronously) from file `prompt.md`.

  If `config.json` contains unexpected data or something that can't be parsed
  (or the prompt can't be loaded), raises an exception.
  """
  raise NotImplementedError()  # {{🍄 load agent config}}


async def load_config(path: pathlib.Path) -> SwarmConfig:
  """Loads the configuration from JSON file in `path`.

  If `telegram` is present, `telegram.token` MUST be set.
  If `telegram.token` is set:

  * `telegram.authorized_users` MUST NOT be empty.
  * `telegram.consumer_agent` MUST be set to a key in `agents`.
  * `telegram.end_user_identity` MUST NOT be a key in `agents`.

  The file in `path` does not contain the agent identity configuration, only an
  "agents" key with a list[str]. The entries in the list are names of agents
  (e.g., "coding" or "receptionist"). We use `_load_agent_identity_config` on
  those directories.

  If any configuration contains unexpected keys (or any data that can't be
  parsed successfully, raises a ValueError with a good description of the
  problem (including the location).
  """
  raise NotImplementedError()  # {{🍄 load config}}
