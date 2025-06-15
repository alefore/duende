import unittest
from parsing import ExtractCommands
from agent_command import CommandInput


class TestExtractCommands(unittest.TestCase):

  def test_single_line_command_without_arguments(self):
    response = "#command"
    expected_output = [CommandInput(command_name="command", arguments=[])]
    self.assertEqual(ExtractCommands(response), expected_output)

  def test_single_line_command_with_arguments(self):
    response = "#command arg1 arg2"
    expected_output = [
        CommandInput(command_name="command", arguments=["arg1", "arg2"])
    ]
    self.assertEqual(ExtractCommands(response), expected_output)

  def test_multiline_command(self):
    response = "#command arg1 <<\nline1\nline2\n#end"
    expected_output = [
        CommandInput(
            command_name="command",
            arguments=["arg1"],
            multiline_content=["line1", "line2"])
    ]
    self.assertEqual(ExtractCommands(response), expected_output)

  def test_multiple_commands(self):
    response = "#command1 arg1\n#command2 arg2 <<\nline1\n#end\n#command3"
    expected_output = [
        CommandInput(command_name="command1", arguments=["arg1"]),
        CommandInput(
            command_name="command2",
            arguments=["arg2"],
            multiline_content=["line1"]),
        CommandInput(command_name="command3", arguments=[])
    ]
    self.assertEqual(ExtractCommands(response), expected_output)

  def test_command_with_special_characters_using_shlex(self):
    response = '#command "arg1 with spaces" arg2'
    expected_output = [
        CommandInput(
            command_name="command", arguments=["arg1 with spaces", "arg2"])
    ]
    self.assertEqual(ExtractCommands(response), expected_output)

  def test_invalid_shlex_argument_handling(self):
    response = "#command 'unterminated quote"
    expected_output = [
        CommandInput(command_name="command", arguments=["'unterminated quote"])
    ]
    self.assertEqual(ExtractCommands(response), expected_output)

  def test_commands_with_random_non_command_text_in_between(self):
    response = "Random text not a command\n#command1 arg1\nMore random text\n#command2 arg2"
    expected_output = [
        CommandInput(command_name="command1", arguments=["arg1"]),
        CommandInput(command_name="command2", arguments=["arg2"])
    ]
    self.assertEqual(ExtractCommands(response), expected_output)

  def test_command_with_multiple_arguments_begin_multiline_block(self):
    response = "#command arg1 arg2 arg3 <<\nmulti-line content\n#end"
    expected_output = [
        CommandInput(
            command_name="command",
            arguments=["arg1", "arg2", "arg3"],
            multiline_content=["multi-line content"])
    ]
    self.assertEqual(ExtractCommands(response), expected_output)

  def test_multiple_multiline_commands(self):
    response = "#command1 arg1 <<\nline1\n#end\n#command2 arg2 <<\nline2\n#end"
    expected_output = [
        CommandInput(
            command_name="command1",
            arguments=["arg1"],
            multiline_content=["line1"]),
        CommandInput(
            command_name="command2",
            arguments=["arg2"],
            multiline_content=["line2"])
    ]
    self.assertEqual(ExtractCommands(response), expected_output)


if __name__ == '__main__':
  unittest.main()
