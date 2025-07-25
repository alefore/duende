import unittest
from unittest.mock import MagicMock, mock_open, patch
import asyncio

from agent_command import CommandInput
from selection_manager import SelectionManager
from write_file_command import WriteFileCommand


class TestWriteFileCommand(unittest.TestCase):

  def setUp(self):
    self.selection_manager = SelectionManager()

  async def test_write_file_success(self) -> None:
    command_input = CommandInput(
        "write_file", args={
            "path": "test.txt",
            "content": "line1\nline2"
        })
    write_file_command = WriteFileCommand(None, self.selection_manager, None)

    with patch("builtins.open", mock_open()) as mock_file, \
         patch("os.path.exists", return_value=False):
      result = await write_file_command.run(command_input.args)

      self.assertIn("#write_file test.txt: Success with 2 lines written.",
                    result.output)
      self.assertEqual(result.errors, "")
      mock_file.assert_called_once_with("test.txt", "w")
      handle = mock_file()
      handle.write.assert_called_once_with("line1\nline2")

  async def test_write_file_directory_creation(self) -> None:
    command_input = CommandInput(
        "write_file", args={
            "path": "dir/test.txt",
            "content": "line1"
        })
    write_file_command = WriteFileCommand(None, self.selection_manager, None)

    with patch("builtins.open", mock_open()) as mock_file, \
         patch("os.makedirs") as mock_makedirs, \
         patch("os.path.exists", return_value=False):
      result = await write_file_command.run(command_input.args)

      self.assertIn("#write_file dir/test.txt: Success with 1 lines written.",
                    result.output)
      self.assertEqual(result.errors, "")
      mock_makedirs.assert_called_once_with("dir", exist_ok=True)
      mock_file.assert_called_once_with("dir/test.txt", "w")

  async def test_write_file_error(self) -> None:
    command_input = CommandInput(
        "write_file", args={
            "path": "test.txt",
            "content": "line1"
        })
    write_file_command = WriteFileCommand(None, self.selection_manager, None)

    with patch(
        "builtins.open", mock_open()) as mock_file, \
        patch("os.path.exists", return_value=False):
      mock_file.side_effect = IOError("File not found")
      result = await write_file_command.run(command_input.args)

      self.assertEqual(result.output, "")
      self.assertIn("Error writing to test.txt: File not found", result.errors)

  async def test_write_file_with_small_diff(self) -> None:
    path = "test.txt"
    original_content = "line1\nline2\nline3"
    new_content = ["line1", "line2_modified", "line3"]
    command_input = CommandInput(
        "write_file", args={
            "path": path,
            "content": "\n".join(new_content)
        })
    write_file_command = WriteFileCommand(None, self.selection_manager, None)

    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=original_content)) as mock_file:
      result = await write_file_command.run(command_input.args)

      self.assertIn(
          f"#{write_file_command.Name()} {path}: Success with 3 lines written.",
          result.output)
      self.assertIn("```diff", result.output)
      self.assertIn("--- a/test.txt", result.output)
      self.assertIn("+++ b/test.txt", result.output)
      self.assertIn("-line2", result.output)
      self.assertIn("+line2_modified", result.output)
      self.assertIn("```", result.output)
      mock_file.assert_any_call(path, "r")
      mock_file.assert_any_call(path, "w")

  async def test_write_file_with_large_diff(self) -> None:
    path = "large_file.txt"
    original_content = [f"line{i}" for i in range(30)]
    new_content = [f"new_line{i}" for i in range(30)]
    command_input = CommandInput(
        "write_file", args={
            "path": path,
            "content": "\n".join(new_content)
        })
    write_file_command = WriteFileCommand(None, self.selection_manager, None)

    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="\n".join(original_content))) as mock_file:
      result = await write_file_command.run(command_input.args)

      self.assertIn(
          f"#{write_file_command.Name()} {path}: Success with 30 lines written.",
          result.output)
      self.assertIn(
          "Diff is too large. Summary: 30 lines added, 30 lines removed.",
          result.output)
      mock_file.assert_any_call(path, "r")
      mock_file.assert_any_call(path, "w")


if __name__ == '__main__':
  unittest.main()
