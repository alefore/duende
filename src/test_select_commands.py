import os
import re
import unittest
from unittest.mock import MagicMock
from agent_command import CommandInput, CommandOutput
from select_commands import SelectCommand, SelectOverwriteCommand
from selection_manager import SelectionManager, StartPatternNotFound, EndPatternNotFound
from file_access_policy import FileAccessPolicy
from validation import ValidationManager


class TestSelectCommands(unittest.TestCase):

  def setUp(self):
    self.file_access_policy = MagicMock(FileAccessPolicy)
    self.selection_manager = SelectionManager()
    self.validation_manager = MagicMock(ValidationManager)

    self.select_literal_cmd = SelectCommand(
        self.file_access_policy, self.selection_manager, use_regex=False)
    self.select_regex_cmd = SelectCommand(
        self.file_access_policy, self.selection_manager, use_regex=True)

    self.select_overwrite_cmd = SelectOverwriteCommand(self.selection_manager,
                                                       self.validation_manager)
    self.file_access_policy.allow_access.return_value = True

    self.test_file_path = "test_file.txt"
    with open(self.test_file_path, "w") as f:
      f.write("START\n")
      f.write("some content\n")
      f.write("END\n")

    self.test_regex_file_path = "test_file_regex.txt"
    with open(self.test_regex_file_path, "w") as f:
      f.write("Start of the content\n")
      f.write("some content here\n")
      f.write("End of the content\n")

  def tearDown(self):
    if os.path.exists(self.test_file_path):
      os.remove(self.test_file_path)
    if os.path.exists(self.test_regex_file_path):
      os.remove(self.test_regex_file_path)

  def test_select_valid_selection(self):
    command_input = CommandInput(
        'select', arguments=[self.test_file_path, 'START', 'END'])

    command_output = self.select_literal_cmd.Execute(command_input)
    self.assertEqual(len(command_output.errors), 0)
    self.assertEqual([
        "select <<", "START", "some content", "END",
        f"#end ({self.test_file_path})"
    ], command_output.output)

  def test_select_no_start_match(self):
    start_pattern = 'UNKNOWN.START'
    command_input = CommandInput(
        'select', arguments=[self.test_file_path, start_pattern, 'END'])

    command_output = self.select_literal_cmd.Execute(command_input)
    self.assertEqual(len(command_output.errors), 1)
    expected_error = f"select: Could not find start pattern '{start_pattern}' in {self.test_file_path}."
    self.assertEqual(command_output.errors[0], expected_error)

  def test_select_no_end_match(self):
    end_pattern = 'UNKNOWN.END'
    command_input = CommandInput(
        'select', arguments=[self.test_file_path, 'START', end_pattern])

    command_output = self.select_literal_cmd.Execute(command_input)
    self.assertEqual(len(command_output.errors), 1)
    expected_error = f"select: Could not find end pattern '{end_pattern}' in {self.test_file_path} after finding start pattern."
    self.assertEqual(command_output.errors[0], expected_error)

  def test_select_regex(self):
    command_input = CommandInput(
        'select_regex',
        arguments=[self.test_regex_file_path, '^Start.*', '^End.*'])

    command_output = self.select_regex_cmd.Execute(command_input)
    self.assertEqual(len(command_output.errors), 0)
    self.assertEqual([
        "select <<", "Start of the content", "some content here",
        "End of the content", f"#end ({self.test_regex_file_path})"
    ], command_output.output)

  def test_select_regex_no_start_match(self):
    start_pattern = 'UNKNOWN\\..*START'
    command_input = CommandInput(
        'select_regex',
        arguments=[self.test_regex_file_path, start_pattern, 'END'])
    command_output = self.select_regex_cmd.Execute(command_input)
    self.assertEqual(len(command_output.errors), 1)
    expected_error = f"select_regex: Could not find start pattern '{start_pattern}' in {self.test_regex_file_path}."
    self.assertEqual(command_output.errors[0], expected_error)

  def test_select_regex_no_end_match(self):
    end_pattern = 'UNKNOWN\\..*END'
    command_input = CommandInput(
        'select_regex',
        arguments=[self.test_regex_file_path, '^Start.*', end_pattern])
    command_output = self.select_regex_cmd.Execute(command_input)
    self.assertEqual(len(command_output.errors), 1)
    expected_error = f"select_regex: Could not find end pattern '{end_pattern}' in {self.test_regex_file_path} after finding start pattern."
    self.assertEqual(command_output.errors[0], expected_error)

  def testSelect_singlePattern_literal(self):
    command_input = CommandInput(
        'select', arguments=['test_file.txt', 'Target Line'])

    with open("test_file.txt", "w") as f:
      f.write("Line 1\n")
      f.write("Target Line\n")
      f.write("Line 3\n")

    command_output = self.select_literal_cmd.Execute(command_input)
    self.assertEqual(len(command_output.errors), 0)
    self.assertEqual(["select <<", "Target Line", "#end (test_file.txt)"],
                     command_output.output)
    self.assertIsNotNone(self.selection_manager.get_selection())
    self.assertEqual(self.selection_manager.get_selection().Read(),
                     ["Target Line"])

  def testSelect_singlePattern_regex(self):
    command_input = CommandInput(
        'select_regex', arguments=['test_file_regex.txt', '.*Target Line.*'])

    with open("test_file_regex.txt", "w") as f:
      f.write("Line 1\n")
      f.write("This is a Target Line for regex\n")
      f.write("Line 3\n")

    command_output = self.select_regex_cmd.Execute(command_input)
    self.assertEqual(len(command_output.errors), 0)
    self.assertEqual([
        "select <<", "This is a Target Line for regex",
        "#end (test_file_regex.txt)"
    ], command_output.output)
    self.assertIsNotNone(self.selection_manager.get_selection())
    self.assertEqual(self.selection_manager.get_selection().Read(),
                     ["This is a Target Line for regex"])

  def test_select_overwrite_no_selection(self):
    command_input = CommandInput(
        'select_overwrite', [], multiline_content=["New content"])
    command_output = self.select_overwrite_cmd.Execute(command_input)
    self.assertGreater(len(command_output.errors), 0)

  def test_select_empty_region(self):
    command_input = CommandInput(
        'select', arguments=['test_file.txt', 'START', 'END'])

    with open("test_file.txt", "w") as f:
      f.write("START\n")
      f.write("END\n")

    command_output = self.select_literal_cmd.Execute(command_input)
    self.assertEqual(len(command_output.errors), 0)
    self.assertEqual(["select <<", "START", "END", "#end (test_file.txt)"],
                     command_output.output)


if __name__ == '__main__':
  unittest.main()
