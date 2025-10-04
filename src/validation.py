import os
import subprocess
import logging
from typing import NamedTuple
import asyncio
from abc import ABC, abstractmethod


class ValidationResult(NamedTuple):
  success: bool
  output: str
  error: str


class ValidationManager(ABC):

  def __init__(self) -> None:
    self.validation_output: ValidationResult | None = None

  def RegisterChange(self) -> None:
    self.validation_output = None

  @abstractmethod
  async def Validate(self) -> ValidationResult:
    pass


class ValidateShellValidationManager(ValidationManager):

  def __init__(self) -> None:
    super().__init__()
    self.validation_script: str = "agent/validate.sh"

  async def Validate(self) -> ValidationResult:
    if self.validation_output is None:
      self.validation_output = await self._execute_validation_script()

      if not self.validation_output.success:
        logging.error(
            f"Validation failed: {self.validation_output.error}")
      else:
        logging.info("Validation succeeded.")

    return self.validation_output

  async def _execute_validation_script(self) -> ValidationResult:
    try:
      process = await asyncio.create_subprocess_exec(
          self.validation_script,
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE,
      )
      stdout, stderr = await process.communicate()
      return ValidationResult(
          success=process.returncode == 0,
          output=stdout.decode().strip(),
          error=stderr.decode().strip())
    except Exception as e:
      logging.error(f"Error executing validation script: {str(e)}")
      return ValidationResult(success=False, output="", error=str(e))


def CreateValidationManager() -> ValidationManager | None:
  script_path = "agent/validate.sh"
  if not os.path.isfile(script_path):
    logging.info(f"{script_path}: Validation script does not exist.")
    return None
  if not os.access(script_path, os.X_OK):
    logging.info(f"{script_path}: Validation script is not executable.")
    return None

  return ValidateShellValidationManager()
