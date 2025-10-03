import unittest
import asyncio
import os
import tempfile
import shutil
import aiofiles
import pathlib
import re

from search_file_command import SearchFileCommand
from file_access_policy import CurrentDirectoryFileAccessPolicy, RegexFileAccessPolicy
from agent_command import CommandOutput


class SearchFileCommandTest(unittest.IsolatedAsyncioTestCase):

  def setUp(self):
    self.original_cwd = os.getcwd()
    self.temp_dir = pathlib.Path(tempfile.mkdtemp())
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

  async def test_run_single_file_single_match(self):
    """Verify correct reporting of a single match in a specified file."""
    file_name = "single_match_file.txt"
    search_term = "unique_term"
    file_content = f"This line has a {search_term} here.\nAnother line.\n"
    async with aiofiles.open(file_name, mode='w') as f:
      await f.write(file_content)

    command = SearchFileCommand(file_access_policy=self.file_access_policy)
    inputs = {'content': search_term, 'path': file_name}
    output: CommandOutput = await command.run(inputs)

    expected_output_line = f"{file_name}:1: This line has a {search_term} here."
    self.assertIn(expected_output_line, output.output)
    self.assertEqual(output.errors, "")
    self.assertIn("Searched 1 files, found 1 matches.", output.summary)

  async def test_run_single_file_multiple_matches(self):
    """Verify correct reporting of multiple matches in a specified file. Validate that lines that don't match don't get returned."""
    file_name = "multiple_match_file.txt"
    search_term = "match"
    file_content = (f"This line has a {search_term}.\n"
                    f"Another line with a {search_term} too.\n"
                    "This line has no relevant word.\n"
                    f"Final line with a {search_term}.\n")
    async with aiofiles.open(file_name, mode='w') as f:
      await f.write(file_content)

    command = SearchFileCommand(file_access_policy=self.file_access_policy)
    inputs = {'content': search_term, 'path': file_name}
    output: CommandOutput = await command.run(inputs)

    expected_output_lines = [
        f"{file_name}:1: This line has a {search_term}.",
        f"{file_name}:2: Another line with a {search_term} too.",
        f"{file_name}:4: Final line with a {search_term}."
    ]

    for line in expected_output_lines:
      self.assertIn(line, output.output)
    self.assertEqual(output.errors, "")
    self.assertIn("Searched 1 files, found 3 matches.", output.summary)

  async def test_run_multiple_files_multiple_matches(self):
    """Verify correct reporting of matches across multiple files."""
    file_name1 = "file1.txt"
    file_name2 = "file2.txt"
    search_term = "test"

    file_content1 = f"This is a {search_term} line.\nAnother line.\n{search_term}ing again.\n"
    file_content2 = f"A {search_term} in a different file.\nNo match here.\n"

    async with aiofiles.open(file_name1, mode='w') as f:
      await f.write(file_content1)
    async with aiofiles.open(file_name2, mode='w') as f:
      await f.write(file_content2)

    command = SearchFileCommand(file_access_policy=self.file_access_policy)
    inputs = {'content': search_term, 'path': None}
    output: CommandOutput = await command.run(inputs)

    expected_output_lines = [
        f"{file_name1}:1: This is a {search_term} line.",
        f"{file_name1}:3: {search_term}ing again.",
        f"{file_name2}:1: A {search_term} in a different file.",
    ]

    for line in expected_output_lines:
      self.assertIn(line, output.output)

    self.assertEqual(output.errors, "")
    self.assertIn("Searched 2 files, found 3 matches.", output.summary)

  async def test_run_with_path_argument(self):
    """Verify search is restricted to the specified file when 'path' argument is used."""
    file_to_search = "target_file.txt"
    other_file = "another_file.txt"
    search_term = "important_word"

    async with aiofiles.open(file_to_search, mode='w') as f:
      await f.write(f"Line one with the {search_term}.\nLine two.\n")
    async with aiofiles.open(other_file, mode='w') as f:
      await f.write(f"This file also has the {search_term}.\n")

    command = SearchFileCommand(file_access_policy=self.file_access_policy)
    inputs = {'content': search_term, 'path': file_to_search}
    output: CommandOutput = await command.run(inputs)

    expected_output_line = f"{file_to_search}:1: Line one with the {search_term}."

    self.assertIn(expected_output_line, output.output)
    self.assertNotIn(other_file, output.output)
    self.assertEqual(output.errors, "")
    self.assertIn("Searched 1 files, found 1 matches.", output.summary)

  async def test_run_repository_wide_search(self):
    """Verify search covers the entire repository, including subdirectories, when no 'path' argument is provided."""
    subdir1 = pathlib.Path("subdir1")
    subdir2 = pathlib.Path("subdir2")
    subdir1.mkdir(exist_ok=True)
    subdir2.mkdir(exist_ok=True)

    file_main = "main_file.txt"
    file_subdir1 = str(subdir1 / "sub_file1.txt")
    file_subdir2 = str(subdir2 / "sub_file2.txt")
    search_term = "repo_match"

    async with aiofiles.open(file_main, mode='w') as f:
      await f.write(f"Here is a {search_term} in the main directory.\n")
    async with aiofiles.open(file_subdir1, mode='w') as f:
      await f.write(f"A {search_term} inside subdir1.\nAnother line.\n")
    async with aiofiles.open(file_subdir2, mode='w') as f:
      await f.write(f"{search_term} is also here in subdir2.\n")

    command = SearchFileCommand(file_access_policy=self.file_access_policy)
    inputs = {'content': search_term, 'path': None}
    output: CommandOutput = await command.run(inputs)

    expected_output_lines = [
        f"{file_main}:1: Here is a {search_term} in the main directory.",
        f"{file_subdir1}:1: A {search_term} inside subdir1.",
        f"{file_subdir2}:1: {search_term} is also here in subdir2."
    ]

    for line in expected_output_lines:
      self.assertIn(line, output.output)

    self.assertEqual(output.errors, "")
    self.assertIn("Searched 3 files, found 3 matches.", output.summary)

  async def test_run_large_number_of_matches(self):
    """Verify correct handling of the match_limit and summary reporting."""
    file_name = "large_match_file.txt"
    search_term = "limit_test"
    num_matches = 250  # More than the default match_limit of 200
    file_content = "\n".join(
        [f"This line has a {search_term}." for _ in range(num_matches)])

    async with aiofiles.open(file_name, mode='w') as f:
      await f.write(file_content)

    command = SearchFileCommand(file_access_policy=self.file_access_policy)
    inputs = {'content': search_term, 'path': file_name}
    output: CommandOutput = await command.run(inputs)

    self.assertIn(f"Too many matches to display ({num_matches}, limit is 200).",
                  output.output)
    self.assertIn(
        f"Files with matches:\npath,lines_match,file_line_count\n{file_name}, {num_matches}, {num_matches}",
        output.output)
    self.assertEqual(output.errors, "")
    self.assertIn(f"Searched 1 files, found {num_matches} matches.",
                  output.summary)

  async def test_run_with_file_access_errors(self):
    """Verify graceful handling and reporting of file access errors (policy-based)."""
    file_allowed = "allowed_file.txt"
    file_restricted = "restricted_file.txt"
    search_term = "policy_test"

    async with aiofiles.open(file_allowed, mode='w') as f:
      await f.write(f"This file is {search_term} and allowed.\n")
    async with aiofiles.open(file_restricted, mode='w') as f:
      await f.write(f"This file is {search_term} but restricted.\n")

    access_policy = RegexFileAccessPolicy(r"^allowed_file\.txt$")
    command = SearchFileCommand(file_access_policy=access_policy)
    inputs = {'content': search_term, 'path': None}
    output: CommandOutput = await command.run(inputs)

    self.assertIn(f"{file_allowed}:1: This file is {search_term} and allowed.",
                  output.output)
    self.assertNotIn(f"{file_restricted}:1:", output.output)

    self.assertEqual(output.errors, "")
    self.assertIn("Searched 1 files, found 1 matches.", output.summary)
    self.assertNotIn("Errors:", output.summary)


if __name__ == '__main__':
  unittest.main()
