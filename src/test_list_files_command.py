import unittest
import os
import tempfile
import shutil
from list_files_command import ListFilesCommand
from agent_command import CommandInput
from file_access_policy import FileAccessPolicy


class TestFileAccessPolicy(FileAccessPolicy):

  def __init__(self) -> None:
    self._denied_paths: set[str] = set()

  def allow_access(self, file_path: str) -> bool:
    return os.path.abspath(file_path) not in self._denied_paths

  def add_denied_path(self, path: str) -> None:
    self._denied_paths.add(os.path.abspath(path))


class TestListFilesCommand(unittest.TestCase):

  def setUp(self):
    self.temp_dir = tempfile.mkdtemp()

    self.file_access_policy = TestFileAccessPolicy()
    self.command = ListFilesCommand(self.file_access_policy)

    self.file1_path = os.path.join(self.temp_dir, 'file1.txt')
    self.file2_path = os.path.join(self.temp_dir, 'file2.txt')
    self.denied_file_path = os.path.join(self.temp_dir, 'denied_file.log')

    self.subdir_path = os.path.join(self.temp_dir, 'subdir')
    os.makedirs(self.subdir_path, exist_ok=True)
    self.subdir_file1_path = os.path.join(self.subdir_path, 'subfile1.py')
    self.subdir_denied_file_path = os.path.join(self.subdir_path,
                                                'subdenied.temp')

    with open(self.file1_path, 'w') as f:
      f.write("content1\nline2")
    with open(self.file2_path, 'w') as f:
      f.write("content2")
    with open(self.denied_file_path, 'w') as f:
      f.write("denied content for policy test")
    with open(self.subdir_file1_path, 'w') as f:
      f.write("import os")
    with open(self.subdir_denied_file_path, 'w') as f:
      f.write("another denied file content")

  def tearDown(self):
    if os.path.exists(self.temp_dir):
      shutil.rmtree(self.temp_dir)

  def _get_expected_output_line(self, file_path, line_count, byte_count):
    """Helper to format expected output lines consistently."""
    return f"{os.path.relpath(file_path, self.temp_dir)}: {line_count} lines, {byte_count} bytes"

  def test_list_files_empty_directory(self):
    empty_dir = tempfile.mkdtemp()  # Use a separate empty dir for this test
    try:
      command_input = CommandInput(
          command_name="list_files", args={'directory': empty_dir})
      output = self.command.run(command_input)
      self.assertEqual([f"Files in '{empty_dir}' <<", f"#end ({empty_dir})"],
                       output.output)
      self.assertIn("Matches: 0", output.summary)
      self.assertEqual(output.errors, [])
    finally:
      shutil.rmtree(empty_dir)  # Clean up this specific empty dir

  def test_list_files_with_all_files_allowed(self):
    command_input = CommandInput(
        command_name="list_files", args={'directory': self.temp_dir})
    output = self.command.run(command_input)

    actual_output_content = output.output[1:-1]  # Strip header/footer.
    actual_output_content = [
        line for line in actual_output_content if line.strip()
    ]  # Remove potential empty lines

    expected_lines = [
        self._get_expected_output_line(self.file1_path, 2,
                                       os.path.getsize(self.file1_path)),
        self._get_expected_output_line(self.file2_path, 1,
                                       os.path.getsize(self.file2_path)),
        self._get_expected_output_line(self.denied_file_path, 1,
                                       os.path.getsize(self.denied_file_path)),
        self._get_expected_output_line(self.subdir_file1_path, 1,
                                       os.path.getsize(self.subdir_file1_path)),
        self._get_expected_output_line(
            self.subdir_denied_file_path, 1,
            os.path.getsize(self.subdir_denied_file_path)),
    ]

    self.assertEqual(sorted(actual_output_content), sorted(expected_lines))
    self.assertIn("Matches: 5", output.summary)
    self.assertEqual(output.errors, [])

  def test_list_files_non_existent_directory(self):
    non_existent_dir = os.path.join(self.temp_dir, "definitely_not_here")
    command_input = CommandInput(
        command_name="list_files", args={'directory': non_existent_dir})
    output = self.command.run(command_input)
    self.assertEqual(output.output, [])
    self.assertIn("Directory not found or is not accessible:", output.errors[0])
    self.assertIn("failed due to inaccessible directory.", output.summary)

  def test_list_files_policy_filters_specific_file_out(self):
    self.file_access_policy.add_denied_path(self.denied_file_path)

    command_input = CommandInput(
        command_name="list_files", args={'directory': self.temp_dir})
    output = self.command.run(command_input)

    for output_line in output.output:  # Denied file should NOT be in output
      self.assertNotIn(
          os.path.relpath(self.denied_file_path, self.temp_dir), output_line)

    # Allowed files should be present
    self.assertIn(
        self._get_expected_output_line(self.file1_path, 2,
                                       os.path.getsize(self.file1_path)),
        output.output)
    self.assertIn(
        self._get_expected_output_line(self.file2_path, 1,
                                       os.path.getsize(self.file2_path)),
        output.output)
    self.assertIn(
        self._get_expected_output_line(self.subdir_file1_path, 1,
                                       os.path.getsize(self.subdir_file1_path)),
        output.output)
    self.assertIn(
        self._get_expected_output_line(
            self.subdir_denied_file_path, 1,
            os.path.getsize(self.subdir_denied_file_path)), output.output)

    # Verify summary count (total files - 1 denied file)
    self.assertIn("Matches: 4", output.summary)  # 5 total files - 1 denied = 4
    self.assertEqual(output.errors, [])

  def test_list_files_policy_allows_content_in_accessible_dir_with_some_denied_content(
      self):
    self.file_access_policy.add_denied_path(self.subdir_denied_file_path)
    self.file_access_policy.add_denied_path(self.denied_file_path)

    command_input = CommandInput(
        command_name="list_files", args={'directory': self.temp_dir})
    output = self.command.run(command_input)

    self.assertIn(
        self._get_expected_output_line(self.file1_path, 2,
                                       os.path.getsize(self.file1_path)),
        output.output)
    self.assertIn(
        self._get_expected_output_line(self.file2_path, 1,
                                       os.path.getsize(self.file2_path)),
        output.output)
    self.assertIn(
        self._get_expected_output_line(self.subdir_file1_path, 1,
                                       os.path.getsize(self.subdir_file1_path)),
        output.output)

    for output_line in output.output:
      self.assertNotIn(
          os.path.relpath(self.denied_file_path, self.temp_dir), output_line)
    for output_line in output.output:
      self.assertNotIn(
          os.path.relpath(self.subdir_denied_file_path, self.temp_dir),
          output_line)

    # Verify summary count (5 total - 2 denied = 3)
    self.assertIn("Matches: 3", output.summary)
    self.assertEqual(output.errors, [])


if __name__ == '__main__':
  unittest.main()
