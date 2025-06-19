import os
from file_access_policy import FileAccessPolicy


def list_all_files(directory: str, file_access_policy: FileAccessPolicy):
  """Generates all file paths in a directory and its subdirectories, sorted."""

  abs_directory = os.path.abspath(directory)
  if not os.path.isdir(abs_directory):
    raise NotADirectoryError(f"{directory} is not a valid directory.")

  for root, _, files in sorted(os.walk(abs_directory)):
    for file in sorted(files):
      file_path = os.path.join(root, file)
      if file_access_policy.allow_access(file_path):
        yield os.path.relpath(file_path, abs_directory)
