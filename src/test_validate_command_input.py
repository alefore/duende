import unittest
from validate_command_input import ValidateCommandInput
from agent_command import CommandSyntax, CommandInput, Argument, ArgumentContentType
from file_access_policy import RegexFileAccessPolicy
import os


class TestValidateCommandInput(unittest.TestCase):

  def setUp(self):
    self.input_path = Argument(
        name="input_path",
        arg_type=ArgumentContentType.PATH_INPUT,
        description="Input file path")
    self.output_path = Argument(
        name="output_path",
        arg_type=ArgumentContentType.PATH_OUTPUT,
        description="Output file path")
    self.file_access_policy = RegexFileAccessPolicy(
        r".*")  # Allow all paths for most tests
    self.restricted_policy = RegexFileAccessPolicy(
        r"^allowed/.*")  # Only allow paths under 'allowed/'

    # Create dummy paths for testing
    self.existing_allowed_path = 'allowed/existing_path'
    self.not_allowed_path = 'not_allowed_path'
    os.makedirs('allowed/', exist_ok=True)
    with open(self.existing_allowed_path, 'w') as f:
      f.write('dummy content')
    with open(self.not_allowed_path, 'w') as f:
      f.write('dummy content')

  def tearDown(self):
    if os.path.exists(self.existing_allowed_path):
      os.remove(self.existing_allowed_path)
    if os.path.exists(self.not_allowed_path):
      os.remove(self.not_allowed_path)
    if os.path.exists('allowed/'):
      os.rmdir('allowed/')

  def test_missing_input_path(self):
    syntax = CommandSyntax(arguments=[self.input_path])
    input = CommandInput(command_name="test_command", args={})
    warnings = ValidateCommandInput(syntax, input, self.file_access_policy)
    self.assertIn("Missing required argument", warnings[0])
    self.assertIn(self.input_path.name, warnings[0])

  def test_excess_arguments_with_no_repeatable_final(self):
    syntax = CommandSyntax(arguments=[self.input_path, self.output_path])
    input = CommandInput(
        command_name="test_command",
        args={
            "input_path": self.existing_allowed_path,
            "output_path": "arg2",
            "extra_arg": "arg3"
        })
    warnings = ValidateCommandInput(syntax, input, self.file_access_policy)
    self.assertIn("Unexpected argument: extra_arg", warnings[0])

  def test_perfect_argument_count(self):
    syntax = CommandSyntax(arguments=[self.input_path, self.output_path])
    input = CommandInput(
        command_name="test_command",
        args={
            "input_path": self.existing_allowed_path,
            "output_path": "arg2"
        })
    warnings = ValidateCommandInput(syntax, input, self.file_access_policy)
    self.assertEqual(warnings, [])

  def test_non_existent_input_path(self):
    syntax = CommandSyntax(arguments=[self.input_path])
    input = CommandInput(
        command_name="test_command", args={"input_path": "non_existent_path"})
    warnings = ValidateCommandInput(syntax, input, self.file_access_policy)
    self.assertIn("File not found", warnings[0])
    self.assertIn(self.input_path.name, warnings[0])
    self.assertIn(input.args[self.input_path.name], warnings[0])

  def test_access_denied_input_path(self):
    syntax = CommandSyntax(arguments=[self.input_path])
    input = CommandInput(
        command_name="test_command", args={"input_path": self.not_allowed_path})
    warnings = ValidateCommandInput(syntax, input, self.restricted_policy)
    self.assertIn("File not found", warnings[0])
    self.assertIn(self.input_path.name, warnings[0])
    self.assertIn(input.args[self.input_path.name], warnings[0])


if __name__ == '__main__':
  unittest.main()
