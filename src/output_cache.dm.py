import asyncio
import hashlib
import os
import pickle
import pathlib
from typing import NamedTuple

from agent_loop_options import AgentLoopOptions, BaseAgentLoop, BaseAgentLoopFactory
from agent_command import VariableName, VariableValueInt, VariableValueStr, VariableValue, VariableMap


class CacheKey(NamedTuple):
  workflow: str
  conversation: str


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


class CachingDelegatingAgentLoop(BaseAgentLoop):

  def __init__(self, workflow: str, cache: OutputCache, delegate: BaseAgentLoop,
               options: AgentLoopOptions):
    self._workflow = workflow
    self._cache = cache
    self._delegate = delegate
    self._options = options

  async def run(self) -> VariableMap:
    key = CacheKey(self._workflow, self._options.conversation.name())
    cache_output = await self._cache.load(key)
    match cache_output:
      case dict(data):
        return data
      case None:
        output = await self._delegate.run()
        await self._cache.save(key, output)
        return output
    assert f"Invalid data: {cache_output}"
    return VariableMap({})


class CachingDelegatingAgentLoopFactory(BaseAgentLoopFactory):

  def __init__(self, workflow: str, cache: OutputCache,
               delegate: BaseAgentLoopFactory) -> None:
    self._workflow = workflow
    self._cache = cache
    self._delegate = delegate

  def new(self, options: AgentLoopOptions) -> BaseAgentLoop:
    return CachingDelegatingAgentLoop(self._workflow, self._cache,
                                      self._delegate.new(options), options)
