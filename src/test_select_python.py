import unittest
from unittest.mock import Mock
from select_python import SelectPythonCommand
from agent_command import CommandInput, CommandOutput
from selection_manager import SelectionManager
import os


class TestSelectPythonCommand(unittest.TestCase):

  def setUp(self):
    self.file_access_policy = Mock()
    self.selection_manager = SelectionManager()
    self.command = SelectPythonCommand(self.file_access_policy,
                                       self.selection_manager)

  def test_execute_with_invalid_arguments(self):
    command_input = CommandInput(command_name="select_python", arguments=[])
    output = self.command.Execute(command_input)
    self.assertIn("requires one or two arguments:", ''.join(output.errors))

  def test_execute_access_denied(self):
    self.file_access_policy.allow_access = Mock(return_value=False)
    command_input = CommandInput(
        command_name="select_python", arguments=["identifier", "dummy/path"])
    output = self.command.Execute(command_input)
    expected_error = "Access to 'dummy/path' is not allowed."
    self.assertIn(expected_error, output.errors[0])

  def test_execute_identifier_not_found(self):
    self.file_access_policy.allow_access = Mock(return_value=True)
    with open("dummy.py", "w") as f:
      f.write("def other_function():\n    pass\n")
    command_input = CommandInput(
        command_name="select_python",
        arguments=["non_existent_function", "dummy.py"])
    output = self.command.Execute(command_input)
    expected_error = "Definition for 'non_existent_function' not found."
    self.assertIn(expected_error, output.summary)
    os.remove("dummy.py")

  def test_execute_complex_file_selection(self):
    self.file_access_policy.allow_access = Mock(return_value=True)
    os.makedirs("src/tests", exist_ok=True)
    code = ("class ComplexClass:\n"
            "    def __init__(self):\n"
            "        self.value = 0\n"
            "    def increment(self):\n"
            "        self.value += 1\n"
            "    @staticmethod\n"
            "    def utility_function(param1, param2):\n"
            "        return param1 + param2\n"
            "    class NestedClass:\n"
            "        def __init__(self, data):\n"
            "            self.data = data\n"
            "        def process(self):\n"
            "            def inner_function(x):\n"
            "                return x * 2\n"
            "            return inner_function(self.data)\n")
    with open("src/tests/sample.py", "w") as f:
      f.write(code)
    command_input = CommandInput(
        command_name="select_python",
        arguments=["ComplexClass", "src/tests/sample.py"])
    output = self.command.Execute(command_input)
    selected_output = "\n".join(output.output).strip()
    selected_output = selected_output.removeprefix('select <<\n').removesuffix(
        '\n#end (selection in src/tests/sample.py)').strip()
    expected_output = code.rstrip()
    self.assertEqual(selected_output, expected_output)
    os.remove("src/tests/sample.py")

  def test_execute_nested_identifier_selection(self):
    self.file_access_policy.allow_access = Mock(return_value=True)
    os.makedirs("src/tests", exist_ok=True)
    code = ("class OuterClass:\n"
            "    def outer_method(self):\n"
            "        pass\n"
            "    class InnerClass:\n"
            "        def __init__(self):\n"
            "            self.name = 'inner'\n"
            "        def inner_method(self):\n"
            "            return self.name\n"
            "        def another_inner_method(self):\n"
            "            pass\n"
            "    def another_outer_method(self):\n"
            "        pass\n"
            "def top_level_func():\n"
            "    pass\n")

    with open("src/tests/nested.py", "w") as f:
      f.write(code)

    # Test nested method within a class
    command_input = CommandInput(
        command_name="select_python",
        arguments=["OuterClass.InnerClass.inner_method", "src/tests/nested.py"])
    output = self.command.Execute(command_input)
    selected_output_lines = [
        line for line in output.output
        if not line.startswith(('select <<', '#end'))
    ]
    expected_method_code = ("        def inner_method(self):\n"
                            "            return self.name")
    self.assertEqual("\n".join(selected_output_lines), expected_method_code)

    # Test nested class
    command_input = CommandInput(
        command_name="select_python",
        arguments=["OuterClass.InnerClass", "src/tests/nested.py"])
    output = self.command.Execute(command_input)
    selected_output_lines = [
        line for line in output.output
        if not line.startswith(('select <<', '#end'))
    ]
    expected_class_code = ("    class InnerClass:\n"
                           "        def __init__(self):\n"
                           "            self.name = 'inner'\n"
                           "        def inner_method(self):\n"
                           "            return self.name\n"
                           "        def another_inner_method(self):\n"
                           "            pass")
    self.assertEqual("\n".join(selected_output_lines), expected_class_code)

    # Test deeply nested function (not explicitly covered by the simple `hasattr(node, 'body')` but should work due to `ast.FunctionDef` having a body).
    # Need to add a deeply nested function to the test code for this.

    # Cleanup
    os.remove("src/tests/nested.py")
    os.rmdir("src/tests")  # Remove the directory after all tests in it are done


if __name__ == "__main__":
  unittest.main()
