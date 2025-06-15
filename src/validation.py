import os
import subprocess
import logging
from typing import Optional


class ValidationManager:

  def __init__(self) -> None:
    self.validation_script: str = "agent/validate.sh"
    self.last_validation_successful: bool = False
    self.contents_changed: bool = False

  def RegisterChange(self) -> None:
    self.contents_changed = True

  def Validate(self) -> subprocess.CompletedProcess:
    if not self.contents_changed and self.last_validation_successful:
      logging.info(
          "No changes detected and last validation was successful. Skipping re-validation."
      )
      return subprocess.CompletedProcess(
          args=[self.validation_script], returncode=0)

    result = self._execute_validation_script()
    self.contents_changed = False
    self.last_validation_successful = (result.returncode == 0)

    if result.returncode != 0:
      logging.error(f"Validation failed: {result.stderr.strip()}")
    else:
      logging.info("Validation succeeded.")

    return result

  def _execute_validation_script(self) -> subprocess.CompletedProcess:
    try:
      return subprocess.run([self.validation_script],
                            capture_output=True,
                            text=True)
    except Exception as e:
      logging.error(f"Error executing validation script: {str(e)}")
      return subprocess.CompletedProcess(
          args=[self.validation_script], returncode=1, stderr=str(e))


def CreateValidationManager() -> Optional[ValidationManager]:
  script_path = "agent/validate.sh"
  if os.path.isfile(script_path) and os.access(script_path, os.X_OK):
    return ValidationManager()
  else:
    logging.info("Validation script is unavailable or not executable.")
    return None
