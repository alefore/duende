import unittest
import os
import shutil
from unittest.mock import Mock, patch

from agent_command import CommandInput, CommandOutput
from select_python import SelectPythonCommand, FindPythonDefinition
from selection_manager import SelectionManager, Selection
from file_access_policy import FileAccessPolicy


class TestSelectPythonCommand(unittest.TestCase):

  def setUp(self):
    self.temp_dir = "temp_test_dir"
    os.makedirs(self.temp_dir, exist_ok=True)
    self.selection_manager = SelectionManager()

  def tearDown(self):
    if os.path.exists(self.temp_dir):
      shutil.rmtree(self.temp_dir)

  def _create_mock_file_access_policy(self, allowed_files: list[str]):
    mock_policy = Mock(spec=FileAccessPolicy)
    mock_policy.allow_access.side_effect = lambda p: p in allowed_files or os.path.isdir(
        p)
    return mock_policy

  def test_execute_no_match(self):
    # Create a dummy python file
    file_path = os.path.join(self.temp_dir, "test_file.py")
    with open(file_path, "w") as f:
      f.write("def another_func(): pass\n")

    mock_file_access_policy = self._create_mock_file_access_policy([file_path])
    command = SelectPythonCommand(mock_file_access_policy,
                                  self.selection_manager)
    command_input = CommandInput(
        command_name="select_python",
        arguments=["non_existent_func", file_path])

    output = command.Execute(command_input)

    self.assertIn("Could not find a definition for 'non_existent_func'.",
                  output.errors)
    self.assertIn("not found", output.summary)
    self.assertIsNone(self.selection_manager.get_selection())

  def test_execute_single_match(self):
    file_path = os.path.join(self.temp_dir, "test_file.py")
    file_content = "class MyClass:\n    def my_method(self):\n        pass\n"
    with open(file_path, "w") as f:
      f.write(file_content)

    mock_file_access_policy = self._create_mock_file_access_policy([file_path])
    command = SelectPythonCommand(mock_file_access_policy,
                                  self.selection_manager)
    command_input = CommandInput(
        command_name="select_python", arguments=["MyClass", file_path])

    output = command.Execute(command_input)

    self.assertIn("select <<", output.output[0])
    self.assertIn("class MyClass:", output.output[1])
    self.assertEqual(len(output.errors), 0)
    # Updated assertion for the new summary format
    self.assertIn("Selected from", output.summary)
    self.assertIn("lines", output.summary)
    self.assertIsNotNone(self.selection_manager.get_selection())
    self.assertEqual(self.selection_manager.get_selection().path, file_path)
    self.assertEqual(self.selection_manager.get_selection().start_index, 0)
    self.assertEqual(self.selection_manager.get_selection().end_index, 2)

  def test_find_python_definition_nested_function(self):
    file_path = os.path.join(self.temp_dir, "nested.py")
    content = """
def outer_func():
    def inner_func():
        pass
"""
    with open(file_path, "w") as f:
      f.write(content)

    mock_policy = self._create_mock_file_access_policy([file_path])
    selections = FindPythonDefinition(mock_policy, file_path,
                                      "outer_func.inner_func")
    self.assertEqual(len(selections), 1)
    self.assertEqual(selections[0].path, file_path)
    # Check lines (adjusting for 0-based index and actual content)
    self.assertEqual(selections[0].start_index, 2)
    self.assertEqual(selections[0].end_index, 3)

  def test_find_python_definition_method_in_class(self):
    file_path = os.path.join(self.temp_dir, "class_method.py")
    content = """
class MyClass:
    def __init__(self):
        pass
    def my_method(self, arg):
        # Some comment
        return arg * 2
"""
    with open(file_path, "w") as f:
      f.write(content)

    mock_policy = self._create_mock_file_access_policy([file_path])
    selections = FindPythonDefinition(mock_policy, file_path,
                                      "MyClass.my_method")
    self.assertEqual(len(selections), 1)
    self.assertEqual(selections[0].path, file_path)
    # Adjust for 0-based index and actual content: 'def my_method' is line 5, index 4
    self.assertEqual(selections[0].start_index, 4)
    self.assertEqual(selections[0].end_index,
                     6)  # Last line of method: 'return arg * 2'


if __name__ == '__main__':
  unittest.main()
