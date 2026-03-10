import unittest
import asyncio
import os
import tempfile
import shutil
import aiofiles
import pathlib
import re

from file_access_policy import CurrentDirectoryFileAccessPolicy, RegexFileAccessPolicy
from agent_command import CommandOutput
from list_files import list_all_files


class ListAllFilesTest(unittest.IsolatedAsyncioTestCase):
  """Contains a good set of tests for `list_all_files`."""

  def setUp(self) -> None:
    self.original_cwd = os.getcwd()
    self.temp_dir = pathlib.Path(tempfile.mkdtemp())
    os.chdir(self.temp_dir)
    self._setUpInitialStructure()

  def _setUpInitialStructure(self) -> None:
    """Sets up the following structure (with empty files):

    animals/mammals: dog.txt, cat.txt, fox.txt
    animals/birds: tucan.jpg, condor.txt
    fruits: banana.md, orange.md
    """
    # {{🍄 create directory structure}}

  def tearDown(self) -> None:
    os.chdir(self.original_cwd)
    shutil.rmtree(self.temp_dir)

  async def testRoot(self) -> None:
    """Root search (".") finds expected number of files."""
    # {{🍄 root}}

  async def testRootFormat(self) -> None:
    """The output of root search (".") is as expected.

    Expected format: "fruits/banana.md"."""
    # {{🍄 expected output root}}

  async def testEmpty(self) -> None:
    """No files are returned for a search in an empty directory."""
    # {{🍄 empty}}

  async def testFlat(self) -> None:
    """Search in a flat directory returns expected number of outputs."""
    # {{🍄 flat}}

  async def testFlatFormat(self) -> None:
    """Search in flat directory returns entries with expected format.

    Expected format: "animals/birds/condor.txt"."""
    # {{🍄 flat format}}

  async def testNestedDirs(self) -> None:
    """Search in animals outputs five entries in the expected format."""
    # {{🍄 nested dirs}}

  async def testFileAccessPolicy(self) -> None:
    """Search in root directory only outputs entries allowed by access policy.

    Creates a regex file access policy matching two files and validates that
    the outputs are exactly as expected."""
    # {{🍄 file access policy}}

  async def testFileAccessPolicyNoMatch(self) -> None:
    """Runs successfully if file access policy doesn't match anything."""
    # {{🍄 file access policy no match}}


if __name__ == '__main__':
  unittest.main()
