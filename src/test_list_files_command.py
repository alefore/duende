import unittest
import os
from list_files_command import ListFilesCommand
from agent_command import CommandInput
from file_access_policy import FileAccessPolicy


class TestFileAccessPolicy(FileAccessPolicy):

  def allow_access(self, file_path: str) -> bool:
    return True


class TestListFilesCommand(unittest.TestCase):

  def setUp(self):
    self.test_dir = '/tmp/test_list_files_command'
    os.makedirs(self.test_dir, exist_ok=True)

    self.file1_path = os.path.join(self.test_dir, 'file1.txt')
    self.file2_path = os.path.join(self.test_dir, 'file2.txt')

    with open(self.file1_path, 'w') as f:
      f.write("Line 1\nLine 2\nLine 3\n")

    with open(self.file2_path, 'w') as f:
      f.write("Line 1\nLine 2\n")

    self.file_access_policy = TestFileAccessPolicy()
    self.command = ListFilesCommand(self.file_access_policy)

  def tearDown(self):
    os.remove(self.file1_path)
    os.remove(self.file2_path)
    os.rmdir(self.test_dir)

  def test_list_files_with_details(self):
    command_input = CommandInput(
        command_name="list_files", arguments=[self.test_dir])
    output = self.command.Execute(command_input).output[0].split('\n')

    # Remove any empty strings from the list
    output = [line for line in output if line.strip()]

    expected_output = [
        f"Files in '{self.test_dir} <<':",
        f"file1.txt: 3 lines, {os.path.getsize(self.file1_path)} bytes",
        f"file2.txt: 2 lines, {os.path.getsize(self.file2_path)} bytes",
        f"#end ({self.test_dir})"
    ]

    self.assertEqual(output, expected_output)


if __name__ == '__main__':
  unittest.main()
