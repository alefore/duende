import unittest
from parsing import ExtractCommands
from agent_command import CommandInput


class TestExtractCommands(unittest.TestCase):

  def test_single_line_command_without_arguments(self):
    response = "#command"
    expected_commands = [CommandInput(command_name="command", arguments=[])]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response), (expected_commands, expected_non_commands))

  def test_single_line_command_with_arguments(self):
    response = "#command arg1 arg2"
    expected_commands = [
        CommandInput(command_name="command", arguments=["arg1", "arg2"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response), (expected_commands, expected_non_commands))

  def test_multiline_command(self):
    response = "#command arg1 <<\nline1\nline2\n#end"
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg1"],
            multiline_content=["line1", "line2"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response), (expected_commands, expected_non_commands))

  def test_multiline_command_with_empty_lines(self):
    response = "#command arg1 <<\nfoo\n\nbar\n#end"
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg1"],
            multiline_content=["foo", "", "bar"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response), (expected_commands, expected_non_commands))

  def test_multiline_command_with_eof_marker(self):
    response = "#command arg1 <<EOF\nline1\nline2\nEOF"
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg1"],
            multiline_content=["line1", "line2"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response), (expected_commands, expected_non_commands))

  def test_multiline_command_with_custom_marker(self):
    response = "#command arg1 <<CUSTOM\nline1\nCUSTOM"
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg1"],
            multiline_content=["line1"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response), (expected_commands, expected_non_commands))

  def test_multiple_commands_with_various_markers(self):
    response = "#command1 arg1 <<EOF\nline1\nEOF\n#command2 <<END\nline2\nEND"
    expected_commands = [
        CommandInput(
            command_name="command1",
            arguments=["arg1"],
            multiline_content=["line1"]),
        CommandInput(
            command_name="command2", arguments=[], multiline_content=["line2"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response), (expected_commands, expected_non_commands))

  def test_multiple_commands(self):
    response = "#command1 arg1\n#command2 arg2 <<\nline1\n#end\n#command3"
    expected_commands = [
        CommandInput(command_name="command1", arguments=["arg1"]),
        CommandInput(
            command_name="command2",
            arguments=["arg2"],
            multiline_content=["line1"]),
        CommandInput(command_name="command3", arguments=[])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response), (expected_commands, expected_non_commands))

  def test_command_with_special_characters_using_shlex(self):
    response = '#command "arg1 with spaces" arg2'
    expected_commands = [
        CommandInput(
            command_name="command", arguments=["arg1 with spaces", "arg2"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response), (expected_commands, expected_non_commands))

  def test_invalid_shlex_argument_handling(self):
    response = "#command 'unterminated quote"
    expected_commands = [
        CommandInput(command_name="command", arguments=["'unterminated quote"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response), (expected_commands, expected_non_commands))

  def test_commands_with_random_non_command_text_in_between(self):
    response = "Random text not a command\n#command1 arg1\nMore random text\n#command2 arg2"
    expected_commands = [
        CommandInput(command_name="command1", arguments=["arg1"]),
        CommandInput(command_name="command2", arguments=["arg2"])
    ]
    expected_non_commands = ["Random text not a command", "More random text"]
    self.assertEqual(
        ExtractCommands(response), (expected_commands, expected_non_commands))

  def test_command_with_multiple_arguments_begin_multiline_block(self):
    response = "#command arg1 arg2 arg3 <<\nmulti-line content\n#end"
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg1", "arg2", "arg3"],
            multiline_content=["multi-line content"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response), (expected_commands, expected_non_commands))

  def test_only_non_command_lines(self):
    response = "This is a simple text.\nJust some random words."
    expected_commands = []
    expected_non_commands = [
        "This is a simple text.", "Just some random words."
    ]
    self.assertEqual(
        ExtractCommands(response), (expected_commands, expected_non_commands))

  def test_interspersed_commands_and_non_commands(self):
    response = "Some intro text.\n#command1 arg1\nMiddle text\n#command2\nEnding text."
    expected_commands = [
        CommandInput(command_name="command1", arguments=["arg1"]),
        CommandInput(command_name="command2", arguments=[])
    ]
    expected_non_commands = ["Some intro text.", "Middle text", "Ending text."]
    self.assertEqual(
        ExtractCommands(response), (expected_commands, expected_non_commands))


if __name__ == '__main__':
  unittest.main()
