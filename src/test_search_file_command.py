import unittest
import asyncio
import os
import tempfile
import shutil
import aiofiles

from search_file_command import SearchFileCommand
from file_access_policy import CurrentDirectoryFileAccessPolicy
from agent_command import CommandOutput


class SearchFileCommandTest(unittest.IsolatedAsyncioTestCase):

  def setUp(self):
    self.original_cwd = os.getcwd()
    self.temp_dir = tempfile.mkdtemp()
    os.chdir(self.temp_dir)
    self.file_access_policy = CurrentDirectoryFileAccessPolicy()

  def tearDown(self):
    os.chdir(self.original_cwd)
    shutil.rmtree(self.temp_dir)

  async def test_run_no_matches(self):
    file_name = "test_file.txt"
    async with aiofiles.open(file_name, mode='w') as f:
      await f.write("Line 1 with unique content.\n")
      await f.write("Line 2 without the search term.\n")

    command = SearchFileCommand(file_access_policy=self.file_access_policy)
    search_term = 'nonexistent_word'
    inputs = {'content': search_term, 'path': None}
    output: CommandOutput = await command.run(inputs)

    self.assertIn(f"No matches found for '{search_term}'.", output.output)
    self.assertEqual(output.errors, "")
    self.assertIn("Searched 1 files, found 0 matches.", output.summary)


if __name__ == '__main__':
  unittest.main()
