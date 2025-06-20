import unittest
from validate_command_input import ValidateCommandInput
from agent_command import CommandSyntax, CommandInput, Argument, ArgumentContentType, ArgumentMultiline
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
    self.multiline = ArgumentMultiline(
        required=True, description="Contents of the file")
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
    syntax = CommandSyntax(required=[self.input_path], optional=[])
    input = CommandInput(command_name="test_command", arguments=[])
    warnings = ValidateCommandInput(syntax, input, self.file_access_policy)
    self.assertIn("Missing required arguments", warnings[0])
    self.assertIn(self.input_path.name, warnings[0])

  def test_excess_arguments_with_no_repeatable_final(self):
    syntax = CommandSyntax(
        required=[self.input_path], optional=[self.output_path])
    input = CommandInput(
        command_name="test_command", arguments=["arg1", "arg2", "arg3"])
    warnings = ValidateCommandInput(syntax, input, self.file_access_policy)
    self.assertIn("Too many arguments provided", warnings[0])
    self.assertNotIn("arg1", warnings[0])
    self.assertNotIn("arg2", warnings[0])
    self.assertIn("arg3", warnings[0])

  def test_perfect_argument_count(self):
    syntax = CommandSyntax(
        required=[self.input_path], optional=[self.output_path])
    input = CommandInput(
        command_name="test_command",
        arguments=[self.existing_allowed_path, "arg2"])
    warnings = ValidateCommandInput(syntax, input, self.file_access_policy)
    self.assertEqual(len(warnings), 0)

  def test_excess_arguments_with_repeatable_final(self):
    repeatable_final_arg = Argument(
        name="extra",
        arg_type=ArgumentContentType.STRING,
        description="Extra arguments")
    syntax = CommandSyntax(
        required=[self.input_path],
        optional=[self.output_path],
        repeatable_final=repeatable_final_arg)
    input = CommandInput(
        command_name="test_command",
        arguments=[self.existing_allowed_path, "arg2", "extra1", "extra2"])
    warnings = ValidateCommandInput(syntax, input, self.file_access_policy)
    self.assertEqual(len(warnings), 0)

  def test_non_existent_input_path(self):
    syntax = CommandSyntax(required=[self.input_path])
    input = CommandInput(
        command_name="test_command", arguments=["non_existent_path"])
    warnings = ValidateCommandInput(syntax, input, self.file_access_policy)
    self.assertIn("File not found", warnings[0])
    self.assertIn(self.input_path.name, warnings[0])
    self.assertIn(input.arguments[0], warnings[0])

  def test_access_denied_input_path(self):
    syntax = CommandSyntax(required=[self.input_path])
    input = CommandInput(
        command_name="test_command", arguments=[self.not_allowed_path])
    warnings = ValidateCommandInput(syntax, input, self.restricted_policy)
    self.assertIn("File not found", warnings[0])
    self.assertIn(self.input_path.name, warnings[0])
    self.assertIn(input.arguments[0], warnings[0])

  def test_path_exists_but_not_allowed(self):
    syntax = CommandSyntax(required=[self.input_path])
    input = CommandInput(
        command_name="test_command", arguments=[self.not_allowed_path])
    warnings = ValidateCommandInput(syntax, input, self.restricted_policy)
    self.assertIn("File not found", warnings[0])
    self.assertIn(self.input_path.name, warnings[0])
    self.assertIn(self.not_allowed_path, warnings[0])

  def test_unexpected_multiline_content(self):
    syntax = CommandSyntax(required=[self.input_path])
    input = CommandInput(
        command_name="test_command",
        arguments=[self.existing_allowed_path],
        multiline_content=["line1", "line2"])
    warnings = ValidateCommandInput(syntax, input, self.file_access_policy)
    self.assertIn("Unexpected multiline content provided", warnings[0])

  def test_missing_required_multiline_content(self):
    syntax = CommandSyntax(required=[self.input_path], multiline=self.multiline)
    input = CommandInput(
        command_name="test_command", arguments=[self.existing_allowed_path])
    warnings = ValidateCommandInput(syntax, input, self.file_access_policy)
    self.assertIn("Missing required multiline content.", warnings[0])
    self.assertIn(self.multiline.description, warnings[0])

  def test_correct_multiline_content_handling(self):
    syntax = CommandSyntax(required=[self.input_path], multiline=self.multiline)
    input = CommandInput(
        command_name="test_command",
        arguments=[self.existing_allowed_path],
        multiline_content=["line1", "line2"])
    warnings = ValidateCommandInput(syntax, input, self.file_access_policy)
    self.assertEqual(len(warnings), 0)


if __name__ == '__main__':
  unittest.main()
