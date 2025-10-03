import abc
import re
import os


class FileAccessPolicy(abc.ABC):

  @abc.abstractmethod
  def allow_access(self, path: str) -> bool:
    """Determine if the given path is allowed access. The path is the absolute path."""
    pass


class RegexFileAccessPolicy(FileAccessPolicy):

  def __init__(self, regex_pattern: str):
    self.pattern = re.compile(regex_pattern)

  def allow_access(self, path: str) -> bool:
    """Check if a path matches the regex pattern for access"""
    relative_path = os.path.relpath(path, os.getcwd())
    return bool(self.pattern.match(relative_path))


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
