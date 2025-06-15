import os
import unittest
from unittest.mock import MagicMock
from agent_command import CommandInput, CommandOutput
from select_commands import SelectTextCommand, SelectOverwriteCommand
from selection_manager import SelectionManager
from file_access_policy import FileAccessPolicy
from validation import ValidationManager


class TestSelectCommands(unittest.TestCase):

  def setUp(self):
    self.file_access_policy = MagicMock(FileAccessPolicy)
    self.selection_manager = SelectionManager()
    self.validation_manager = MagicMock(ValidationManager)
    self.select_text_cmd = SelectTextCommand(self.file_access_policy,
                                             self.selection_manager)
    self.select_overwrite_cmd = SelectOverwriteCommand(self.selection_manager, self.validation_manager)
    self.file_access_policy.allow_access.return_value = True

  def test_select_valid_selection(self):
    command_input = CommandInput(
        'select', arguments=['test_file.txt', 'START', 'END'])
    self.file_access_policy.allow_access.return_value = True

    with open("test_file.txt", "w") as f:
      f.write("START\n")
      f.write("some content\n")
      f.write("END\n")

    command_output = self.select_text_cmd.Execute(command_input)
    self.assertEqual(len(command_output.errors), 0)
    self.assertIn("select <<\nSTART\nsome content\nEND\n#end (test_file.txt)",
                  command_output.output)

  def test_select_no_match(self):
    command_input = CommandInput(
        'select', arguments=['test_file.txt', 'UNKNOWN_START', 'END'])

    with open("test_file.txt", "w") as f:
      f.write("START\n")
      f.write("some content\n")
      f.write("END\n")

    command_output = self.select_text_cmd.Execute(command_input)
    self.assertGreater(len(command_output.errors), 0)

  def test_select_invalid_arguments(self):
    command_input = CommandInput('select', arguments=['only_one_argument'])
    command_output = self.select_text_cmd.Execute(command_input)
    self.assertGreater(len(command_output.errors), 0)

  def test_select_file_not_found(self):
    command_input = CommandInput(
        'select', arguments=['non_existent_file.txt', 'START', 'END'])
    command_output = self.select_text_cmd.Execute(command_input)
    self.assertGreater(len(command_output.errors), 0)

  def test_select_access_denied(self):
    command_input = CommandInput(
        'select', arguments=['test_file.txt', 'START', 'END'])

    with open("test_file.txt", "w") as f:
      f.write("START\n")

    self.file_access_policy.allow_access.return_value = False
    command_output = self.select_text_cmd.Execute(command_input)
    self.assertGreater(len(command_output.errors), 0)

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

    command_output = self.select_text_cmd.Execute(command_input)
    self.assertEqual(len(command_output.errors), 0)
    self.assertIn("select <<\nSTART\nEND\n#end (test_file.txt)",
                  command_output.output)

  def tearDown(self):
    if os.path.exists("test_file.txt"):
      os.remove("test_file.txt")


if __name__ == '__main__':
  unittest.main()
