import unittest
from unittest.mock import Mock, patch
from replace_python_command import ReplacePythonCommand
from agent_command import CommandInput, CommandOutput
from selection_manager import Selection
from file_access_policy import FileAccessPolicy
from validation import ValidationManager


class TestReplacePythonCommand(unittest.TestCase):

  def setUp(self):
    self.file_access_policy = Mock(spec=FileAccessPolicy)
    self.validation_manager = Mock(spec=ValidationManager)
    self.command = ReplacePythonCommand(self.file_access_policy,
                                        self.validation_manager)

  @patch('replace_python_command.FindPythonDefinition')
  def test_multiple_matches_in_single_file(self, mock_find):
    self.file_access_policy.allow_access.return_value = True

    # Simulate multiple matches in a single file
    mock_find.return_value = [
        Selection('dummy.py', 0, 10),
        Selection('dummy.py', 20, 30)
    ]

    command_input = CommandInput(
        command_name="replace_python",
        arguments=["dummy_function", "dummy.py"],
        multiline_content=[])
    output = self.command.Execute(command_input)

    self.assertIn("Multiple matches found for identifier 'dummy_function'",
                  output.errors[0])


if __name__ == "__main__":
  unittest.main()
