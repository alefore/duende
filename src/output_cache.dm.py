import asyncio
import hashlib
import os
import pickle
import pathlib
from typing import NamedTuple

from agent_command import VariableName, VariableValueInt, VariableValueStr, VariableValue, VariableMap


class CacheKey(NamedTuple):
  workflow: str
  conversation: str
  extra_key: str


DEFAULT_PATH = pathlib.Path.home() / ".duende" / "cache"


class OutputCache:
  """Cache of outputs of conversations."""

  def __init__(self, base_dir: pathlib.Path) -> None:
    self._base_dir = base_dir

  def _get_path_for_key(self, key: CacheKey) -> pathlib.Path:
    """Generates a stable, unique filepath for a given cache key.

    We create a hash from the key to get a safe and unique filename.
    Example: ('workflow_x', 'conversation_x', 'extra_x')
      -> '<cache_dir>/<sha256_hash>.pkl'

    The hash is a function of all parameters in `key`.

    {{🦔 Output is a file directly in `self._base_dir`.}}
    {{🦔 Changing any of the parameters in `key` results in a different hash.}}
    """
    raise NotImplementedError()  # {{🍄 get path for key}}

  async def save(self, key: CacheKey, value: VariableMap) -> None:
    """Atomically saves a single conversation (VariableMap) to the cache.

    Writes to a temporary file first, then atomically renames it.
    This prevents other processes from reading a half-written file.

    Does not catch exceptions; let's them bubble up.

    {{🦔 Uses async io.}}
    """
    output = self._get_path_for_key(key)
    tmp_output = output.with_suffix(f"{output.suffix}.tmp")
    # {{🍄 create cache dir if it doesn't exist}}
    # {{🍄 use pickle to write both `key` and `value` to tmp_output}}
    # {{🍄 rename tmp_output to output}}

  async def load(self, key: CacheKey) -> VariableMap | None:
    """Loads a single conversation from its cache file.

    Returns None if the file doesn't exist.

    If the file is corrupt, lets exceptions bubble up.

    {{🦔 Uses async io.}}
    """
    filepath = self._get_path_for_key(key)
    if not filepath.exists():
      return None
    raise NotImplementedError()  # {{🍄 use pickle to load `key` and `value`}}
