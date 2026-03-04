import aiofiles
import dataclasses
import json
import pathlib

from swarm_types import AgentName


@dataclasses.dataclass(frozen=True)
class AgentIdentityConfig:
  # Unique name of this agent
  name: AgentName

  capability: list[str]

  prompt_path: pathlib.Path

  file_access_policy_regex: str

  telegram_token: str | None


@dataclasses.dataclass(frozen=True)
class SwarmConfig:
  agents: dict[AgentName, AgentIdentityConfig]
  # Path to the SQLite DB containing the messages queue.
  message_bus_path: pathlib.Path


async def load_config(path: pathlib.Path) -> SwarmConfig:
  """Loads the configuration from JSON file in `path`."""
  raise NotImplementedError()  # {{🍄 load config}}
