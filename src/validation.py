import os
import subprocess
import logging


class ValidationManager:

  def __init__(self):
    self.validation_script = "agent/validate.sh"
    self.last_validation_successful = False
    self.contents_changed = False

  def RegisterChange(self):
    self.contents_changed = True

  def Validate(self):
    if not self._is_script_available():
      logging.info("Validation script is unavailable or not executable.")
      return

    if not self.contents_changed and self.last_validation_successful:
      logging.info(
          "No changes detected and last validation was successful. Skipping re-validation."
      )
      return

    result = self._execute_validation_script()
    self.contents_changed = False
    self.last_validation_successful = (result.returncode == 0)

    if result.returncode != 0:
      logging.error(f"Validation failed: {result.stderr.strip()}")
    else:
      logging.info("Validation succeeded.")

    return result

  def _is_script_available(self):
    return os.path.isfile(self.validation_script) and os.access(
        self.validation_script, os.X_OK)

  def _execute_validation_script(self):
    try:
      return subprocess.run([self.validation_script],
                            capture_output=True,
                            text=True)
    except Exception as e:
      logging.error(f"Error executing validation script: {str(e)}")
      return subprocess.CompletedProcess(
          args=[self.validation_script], returncode=1, stderr=str(e))
