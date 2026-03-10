import unittest
import os
import pathlib
import tempfile
from unittest.mock import MagicMock

from read_file_command import ReadFileCommand
from file_access_policy import FileAccessPolicy
from agent_command import CommandOutput, PATH_VARIABLE_NAME, VariableMap, VariableName, VariableValueInt
from pathbox import PathBox


class TestReadFileCommand(unittest.IsolatedAsyncioTestCase):

  def setUp(self) -> None:
    # Create a temporary file with known content for testing
    self.test_file_content = ("Line 1\n"
                              "Line 2 with some text\n"
                              "Line 3: Another line\n"
                              "Line 4 is here\n"
                              "Last Line: 5")
    self.temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
    self.temp_file.write(self.test_file_content)
    self.temp_file.close()
    self.temp_file_path = pathlib.Path(self.temp_file.name)

    # Mock FileAccessPolicy for testing
    self.read_file_command = ReadFileCommand(PathBox())

  def tearDown(self) -> None:
    # Clean up the temporary file
    os.unlink(self.temp_file_path)

  async def test_read_file_entirely(self) -> None:
    # Test reading the entire file (no start_line or end_line)
    inputs = VariableMap({PATH_VARIABLE_NAME: self.temp_file_path})
    output = await self.read_file_command.run(inputs)
    self.assertIsInstance(output, CommandOutput)
    self.assertEqual(output.output, self.test_file_content)
    self.assertIn("Read file", output.summary)
    self.assertIn("entirely", output.summary)
    self.assertIn("(5 lines).", output.summary)
    self.assertEqual(output.errors, "")

  async def test_read_file_with_start_and_end_line(self) -> None:
    # Test reading with both start_line and end_line
    inputs = VariableMap({
        PATH_VARIABLE_NAME: self.temp_file_path,
        VariableName('start_line'): VariableValueInt(2),
        VariableName('end_line'): VariableValueInt(4)
    })
    expected_content = ("Line 2 with some text\n"
                        "Line 3: Another line\n"
                        "Line 4 is here\n")
    output = await self.read_file_command.run(inputs)
    self.assertIsInstance(output, CommandOutput)
    self.assertEqual(output.output, expected_content)
    self.assertIn("from line 2 to 4.", output.summary)
    self.assertIn("(3 lines).", output.summary)
    self.assertEqual(output.errors, "")

  async def test_read_file_with_only_start_line(self) -> None:
    # Test reading with only start_line
    inputs = VariableMap({
        PATH_VARIABLE_NAME: self.temp_file_path,
        VariableName('start_line'): VariableValueInt(3)
    })
    expected_content = ("Line 3: Another line\n"
                        "Line 4 is here\n"
                        "Last Line: 5")
    output = await self.read_file_command.run(inputs)
    self.assertIsInstance(output, CommandOutput)
    self.assertEqual(output.output, expected_content)
    self.assertIn("from line 3.", output.summary)
    self.assertIn("(3 lines).", output.summary)
    self.assertEqual(output.errors, "")

  async def test_read_file_with_only_end_line(self) -> None:
    # Test reading with only end_line
    inputs = VariableMap({
        PATH_VARIABLE_NAME: self.temp_file_path,
        VariableName('end_line'): VariableValueInt(2)
    })
    expected_content = ("Line 1\n"
                        "Line 2 with some text\n")
    output = await self.read_file_command.run(inputs)
    self.assertIsInstance(output, CommandOutput)
    self.assertEqual(output.output, expected_content)
    self.assertIn("up to line 2.", output.summary)
    self.assertIn("(2 lines).", output.summary)
    self.assertEqual(output.errors, "")

  async def test_read_file_start_line_equals_end_line(self) -> None:
    # Test reading a single line
    inputs = VariableMap({
        PATH_VARIABLE_NAME: self.temp_file_path,
        VariableName('start_line'): VariableValueInt(3),
        VariableName('end_line'): VariableValueInt(3)
    })
    expected_content = "Line 3: Another line\n"
    output = await self.read_file_command.run(inputs)
    self.assertIsInstance(output, CommandOutput)
    self.assertEqual(output.output, expected_content)
    self.assertIn("from line 3 to 3.", output.summary)
    self.assertIn("(1 lines).", output.summary)
    self.assertEqual(output.errors, "")

  async def test_read_file_start_line_out_of_bounds(self) -> None:
    # Test start_line beyond file length
    inputs = VariableMap({
        PATH_VARIABLE_NAME: self.temp_file_path,
        VariableName('start_line'): VariableValueInt(10)
    })
    output = await self.read_file_command.run(inputs)
    self.assertIsInstance(output, CommandOutput)
    self.assertNotEqual(output.errors, "")
    self.assertIn("start_line out of bounds", output.summary)

  async def test_read_file_start_line_greater_than_end_line(self) -> None:
    # Test start_line > end_line
    inputs = VariableMap({
        PATH_VARIABLE_NAME: self.temp_file_path,
        VariableName('start_line'): VariableValueInt(3),
        VariableName('end_line'): VariableValueInt(2)
    })
    output = await self.read_file_command.run(inputs)
    self.assertIsInstance(output, CommandOutput)
    self.assertNotEqual(output.errors, "")
    self.assertIn("start_line cannot be greater than end_line", output.summary)

  async def test_read_file_end_line_beyond_file_length(self) -> None:
    # Test end_line beyond file length (should read till end)
    inputs = VariableMap({
        PATH_VARIABLE_NAME: self.temp_file_path,
        VariableName('start_line'): VariableValueInt(4),
        VariableName('end_line'): VariableValueInt(10)
    })
    expected_content = ("Line 4 is here\n"
                        "Last Line: 5")
    output = await self.read_file_command.run(inputs)
    self.assertIsInstance(output, CommandOutput)
    self.assertEqual(output.output, expected_content)
    self.assertIn("from line 4 to 10.", output.summary)
    self.assertIn("(2 lines).", output.summary)  # Should read 2 lines
    self.assertEqual(output.errors, "")

  async def test_read_file_empty_file(self) -> None:
    # Test reading an empty file
    empty_temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
    empty_temp_file.close()
    empty_temp_file_path = empty_temp_file.name

    inputs = VariableMap(
        {PATH_VARIABLE_NAME: pathlib.Path(empty_temp_file_path)})
    output = await self.read_file_command.run(inputs)
    self.assertIsInstance(output, CommandOutput)
    self.assertEqual(output.output, "")
    self.assertIn("entirely", output.summary)
    self.assertIn("(0 lines).", output.summary)
    self.assertEqual(output.errors, "")
    os.unlink(empty_temp_file_path)

  async def test_read_file_non_existent_file(self) -> None:
    # Test reading a non-existent file
    non_existent_path = "/path/to/non_existent_file.txt"
    inputs = VariableMap({PATH_VARIABLE_NAME: pathlib.Path(non_existent_path)})
    output = await self.read_file_command.run(inputs)
    self.assertIsInstance(output, CommandOutput)
    self.assertNotEqual(output.errors, "")
    self.assertIn("command error", output.summary)
    self.assertIn("No such file or directory", output.errors)
