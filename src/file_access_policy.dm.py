import abc
import aiofiles
import dataclasses
from enum import Enum, auto
import json
import os
import pathlib
import re
from typing import Any


class FileAccessScope(Enum):
  # Don't give file access (default).
  NONE = auto()

  # Allow local directory access.
  LOCAL = auto()

  # Allow access to the entire file system.
  ALL = auto()


class FileAccessHiddenFiles(Enum):
  DENY = auto()
  ALLOW = auto()


@dataclasses.dataclass(frozen=True)
class FileAccessPolicyConfig:
  regex: re.Pattern | None = None

  scope: FileAccessScope = FileAccessScope.NONE

  hidden: FileAccessHiddenFiles = FileAccessHiddenFiles.DENY


def create_file_access_policy_config(
    data: dict[str, Any]) -> FileAccessPolicyConfig:
  """Receives a JSON dictionary and turns it into a config.

  Raises a ValueError exception if it finds any invalid key (or data it can't
  parse).
  """
  raise NotImplementedError()  # {{🍄 create config}}


async def load_file_access_policy(path: pathlib.Path) -> FileAccessPolicyConfig:
  """Loads the configuration from JSON file in `path`.

  Errors from `create_file_access_policy` are augmented with the path and
  re-thrown (to make error reports more useful).
  """
  raise NotImplementedError()  # {{🍄 load config}}


class FileAccessPolicy(abc.ABC):

  @abc.abstractmethod
  def allow_access(self, path: str) -> bool:
    """Determine if the given path is allowed access. The path is the absolute path."""
    pass


class RegexFileAccessPolicy(FileAccessPolicy):

  def __init__(self, pattern: re.Pattern):
    self.pattern = pattern

  def allow_access(self, path: str) -> bool:
    """Check if a path matches the regex pattern for access"""
    relative_path = os.path.relpath(path, os.getcwd())
    return bool(self.pattern.fullmatch(relative_path)) or bool(
        self.pattern.fullmatch(os.path.abspath(path)))


class CurrentDirectoryFileAccessPolicy(FileAccessPolicy):

  def allow_access(self, path: str) -> bool:
    abs_path = os.path.abspath(path)
    cwd = os.path.abspath(os.getcwd())
    return abs_path.startswith(cwd)


class CompositeFileAccessPolicy(FileAccessPolicy):

  def __init__(self, policies: list[FileAccessPolicy]):
    self.policies = policies

  def allow_access(self, path: str) -> bool:
    return all(policy.allow_access(path) for policy in self.policies)


class _PermissiveFileAccessPolicy(FileAccessPolicy):
  """Allows all requests."""
  raise NotImplementedError()  # {{🍄 permissive}}


class _DenyAllFileAccessPolicy(FileAccessPolicy):
  """Denies all requests."""
  raise NotImplementedError()  # {{🍄 deny all}}


class _DenyHiddenFiles(FileAccessPolicy):
  """Denies requests for hidden files/directories."""
  raise NotImplementedError()  # {{🍄 deny hidden}}


def create_file_access_policy(
    config: FileAccessPolicyConfig) -> FileAccessPolicy:
  raise NotImplementedError()  # {{🍄 create policy}}
