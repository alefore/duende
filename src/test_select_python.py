import unittest
from unittest.mock import Mock
from select_python import SelectPythonCommand
from agent_command import CommandInput, CommandOutput
from selection_manager import SelectionManager


class TestSelectPythonCommand(unittest.TestCase):

  def setUp(self):
    self.file_access_policy = Mock()
    self.selection_manager = SelectionManager()
    self.command = SelectPythonCommand(self.file_access_policy,
                                       self.selection_manager)

  def test_get_description(self):
    description = self.command.GetDescription()
    self.assertIn("#select_python <path> <identifier>:", description)

  def test_execute_with_invalid_arguments(self):
    command_input = CommandInput(
        command_name="select_python", arguments=["only_one_argument"])
    output = self.command.Execute(command_input)
    self.assertIn(
        "#select_python requires exactly two arguments: <path> <identifier>.",
        output.errors)

  def test_execute_access_denied(self):
    self.file_access_policy.allow_access = Mock(return_value=False)
    command_input = CommandInput(
        command_name="select_python", arguments=["dummy/path", "identifier"])
    output = self.command.Execute(command_input)
    self.assertIn("Access to 'dummy/path' is not allowed.", output.errors[0])

  def test_execute_identifier_not_found(self):
    self.file_access_policy.allow_access = Mock(return_value=True)
    with open("dummy.py", "w") as f:
      f.write("def other_function():\n    pass\n")
    command_input = CommandInput(
        command_name="select_python",
        arguments=["dummy.py", "non_existent_function"])
    output = self.command.Execute(command_input)
    self.assertIn("Could not find a definition for 'non_existent_function'.",
                  output.errors[0])

  def test_execute_complex_file_selection(self):
    self.file_access_policy.allow_access = Mock(return_value=True)
    command_input = CommandInput(
        command_name="select_python",
        arguments=["src/tests/sample.py", "ComplexClass"])
    output = self.command.Execute(command_input)
    selected_output = "\n".join(output.output).strip()
    selected_output = selected_output.removeprefix('select <<\n').removesuffix(
        '\n#end (selection in src/tests/sample.py)').strip()
    expected_output = ("class ComplexClass:\n"
                       "    def __init__(self):\n"
                       "        self.value = 0\n\n"
                       "    def increment(self):\n"
                       "        self.value += 1\n\n"
                       "    @staticmethod\n"
                       "    def utility_function(param1, param2):\n"
                       "        return param1 + param2\n\n"
                       "    class NestedClass:\n"
                       "        def __init__(self, data):\n"
                       "            self.data = data\n\n"
                       "        def process(self):\n"
                       "            def inner_function(x):\n"
                       "                return x * 2\n"
                       "            return inner_function(self.data)")
    self.assertEqual(selected_output, expected_output)


if __name__ == "__main__":
  unittest.main()
