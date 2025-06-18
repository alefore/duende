import os
import subprocess
import logging
from typing import Optional


class ValidationManager:

  def __init__(self) -> None:
    self.validation_script: str = "agent/validate.sh"
    self.validation_output: Optional[subprocess.CompletedProcess] = None

  def RegisterChange(self) -> None:
    self.validation_output = None

  def Validate(self) -> subprocess.CompletedProcess:
    if self.validation_output is None:
      self.validation_output = self._execute_validation_script()

      if self.validation_output.returncode != 0:
        logging.error(
            f"Validation failed: {self.validation_output.stderr.strip()}")
      else:
        logging.info("Validation succeeded.")

    return self.validation_output

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
  if not os.path.isfile(script_path):
    logging.info(f"{script_path}: Validation script does not exist.")
    return None
  if not os.access(script_path, os.X_OK):
    logging.info(f"{script_path}: Validation script is not executable.")
    return None

  return ValidationManager()
