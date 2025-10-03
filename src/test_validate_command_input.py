import os
import unittest

from agent_command import AgentCommand, CommandSyntax, CommandInput, Argument, ArgumentContentType, VariableMap, VariableName, VariableValueStr
from command_registry import CommandRegistry
from file_access_policy import RegexFileAccessPolicy
from validate_command_input import CommandValidationError, validate_command_input


class FakeCommand(AgentCommand):

  def __init__(self, arguments: list[Argument] = []):
    self._arguments = arguments

  def execute(self):
    assert False

  def Syntax(self):
    return CommandSyntax(name="test_command", arguments=self._arguments)

  def Name(self):
    return self.Syntax().name

  def run(self, inputs: VariableMap):
    pass


def fake_registry(arguments: list[Argument]):
  output = CommandRegistry()
  output.Register(FakeCommand(arguments))
  return output


class TestValidateCommandInput(unittest.TestCase):

  def setUp(self) -> None:
    self.input_path = Argument(
        name=VariableName("input_path"),
        arg_type=ArgumentContentType.PATH_INPUT,
        description="Input file path")
    self.output_path = Argument(
        name=VariableName("output_path"),
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

  def tearDown(self) -> None:
    if os.path.exists(self.existing_allowed_path):
      os.remove(self.existing_allowed_path)
    if os.path.exists(self.not_allowed_path):
      os.remove(self.not_allowed_path)
    if os.path.exists('allowed/'):
      os.rmdir('allowed/')

  def test_missing_input_path(self) -> None:
    input = CommandInput(command_name="test_command", args=VariableMap({}))
    with self.assertRaisesRegex(CommandValidationError,
                                r".*Missing required argument: input_path"):
      validate_command_input(input, fake_registry([self.input_path]),
                             self.file_access_policy)

  def test_excess_arguments_with_no_repeatable_final(self) -> None:
    input = CommandInput(
        command_name="test_command",
        args=VariableMap({
            VariableName("input_path"):
                VariableValueStr(self.existing_allowed_path),
            VariableName("output_path"):
                VariableValueStr("arg2"),
            VariableName("extra_arg"):
                VariableValueStr("arg3")
        }))
    with self.assertRaisesRegex(CommandValidationError,
                                "Unexpected argument: extra_arg"):
      validate_command_input(input,
                             fake_registry([self.input_path, self.output_path]),
                             self.file_access_policy)

  def test_perfect_argument_count(self) -> None:
    input = CommandInput(
        command_name="test_command",
        args=VariableMap({
            VariableName("input_path"):
                VariableValueStr(self.existing_allowed_path),
            VariableName("output_path"):
                VariableValueStr("arg2")
        }))
    validate_command_input(input,
                           fake_registry([self.input_path, self.output_path]),
                           self.file_access_policy)

  def test_non_existent_input_path(self) -> None:
    input = CommandInput(
        command_name="test_command",
        args=VariableMap({
            VariableName("input_path"): VariableValueStr("non_existent_path")
        }))
    with self.assertRaisesRegex(
        CommandValidationError,
        f"{self.input_path.name}.*File not found.*non_existent_path"):
      validate_command_input(input, fake_registry([self.input_path]),
                             self.file_access_policy)

  def test_access_denied_input_path(self) -> None:
    input = CommandInput(
        command_name="test_command",
        args=VariableMap({
            VariableName("input_path"): VariableValueStr(self.not_allowed_path)
        }))
    with self.assertRaisesRegex(
        CommandValidationError,
        r".*test_command.*input_path.*File not found.*not_allowed_path"):
      validate_command_input(input, fake_registry([self.input_path]),
                             self.restricted_policy)


if __name__ == '__main__':
  unittest.main()
