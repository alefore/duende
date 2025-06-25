import subprocess
import os
import logging
from typing import List


def GetGitDiffContent() -> List[str]:
  """Retrieves the git diff output for uncommitted changes."""
  try:
    result = subprocess.run(["git", "diff", "--unified=0"],
                            capture_output=True,
                            text=True,
                            check=True)
    if result.stdout.strip():
      return result.stdout.splitlines()
    else:
      return ["No uncommitted changes (git diff is empty)."]
  except subprocess.CalledProcessError as e:
    logging.error(f"Failed to get git diff: {e}\nStderr: {e.stderr}")
    return [f"Error getting git diff: {e.stderr}"]
  except FileNotFoundError:
    logging.error("Git command not found. Cannot get git diff.")
    return ["Warning: Git command not found. Cannot get git diff."]
  except Exception as e:
    logging.error(f"An unexpected error occurred while getting git diff: {e}")
    return [f"Error getting git diff: {e}"]


def ReadReviewPromptFile(file_path: str = 'agent/review.txt') -> List[str]:
  """Reads the content of the review prompt file."""
  with open(file_path, 'r') as f:
    return [l.rstrip() for l in f.readlines()]
