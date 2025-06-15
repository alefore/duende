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

  def Validate(self) -> Optional[subprocess.CompletedProcess]:
    if not self._is_script_available():
      logging.info("Validation script is unavailable or not executable.")
      return None

    if not self.contents_changed and self.last_validation_successful:
      logging.info(
          "No changes detected and last validation was successful. Skipping re-validation."
      )
      return None

    result = self._execute_validation_script()
    self.contents_changed = False
    self.last_validation_successful = (result.returncode == 0)

    if result.returncode != 0:
      logging.error(f"Validation failed: {result.stderr.strip()}")
    else:
      logging.info("Validation succeeded.")

    return result

  def _is_script_available(self) -> bool:
    return os.path.isfile(self.validation_script) and os.access(
        self.validation_script, os.X_OK)

  def _execute_validation_script(self) -> subprocess.CompletedProcess:
    try:
      return subprocess.run([self.validation_script],
                            capture_output=True,
                            text=True)
    except Exception as e:
      logging.error(f"Error executing validation script: {str(e)}")
      return subprocess.CompletedProcess(
          args=[self.validation_script], returncode=1, stderr=str(e))
