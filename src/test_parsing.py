import unittest
from parsing import ExtractCommands
from agent_command import CommandInput


class TestExtractCommands(unittest.TestCase):

  def test_single_line_command_without_arguments(self):
    response_lines = ["#command"]
    expected_commands = [CommandInput(command_name="command", arguments=[])]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_single_line_command_with_arguments(self):
    response_lines = ["#command arg1 arg2"]
    expected_commands = [
        CommandInput(command_name="command", arguments=["arg1", "arg2"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_multiline_command(self):
    response_lines = ["#command arg1 <<", "line1", "line2", "#end"]
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg1"],
            multiline_content=["line1", "line2"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_multiline_command_with_empty_lines(self):
    response_lines = ["#command arg1 <<", "foo", "", "bar", "#end"]
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg1"],
            multiline_content=["foo", "", "bar"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_multiline_command_with_eof_marker(self):
    response_lines = ["#command arg1 <<EOF", "line1", "line2", "EOF"]
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg1"],
            multiline_content=["line1", "line2"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_multiline_command_with_custom_marker(self):
    response_lines = ["#command arg1 <<CUSTOM", "line1", "CUSTOM"]
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg1"],
            multiline_content=["line1"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_multiple_commands_with_various_markers(self):
    response_lines = ["#command1 arg1 <<EOF", "line1", "EOF", "#command2 <<END", "line2", "END"]
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
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_multiple_commands(self):
    response_lines = ["#command1 arg1", "#command2 arg2 <<", "line1", "#end", "#command3"]
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
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_command_with_special_characters_using_shlex(self):
    response_lines = ['#command "arg1 with spaces" arg2']
    expected_commands = [
        CommandInput(
            command_name="command", arguments=["arg1 with spaces", "arg2"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_invalid_shlex_argument_handling(self):
    response_lines = ["#command 'unterminated quote"]
    expected_commands = [
        CommandInput(command_name="command", arguments=["'unterminated quote"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_commands_with_random_non_command_text_in_between(self):
    response_lines = ["Random text not a command", "#command1 arg1", "More random text", "#command2 arg2"]
    expected_commands = [
        CommandInput(command_name="command1", arguments=["arg1"]),
        CommandInput(command_name="command2", arguments=["arg2"])
    ]
    expected_non_commands = ["Random text not a command", "More random text"]
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_command_with_multiple_arguments_begin_multiline_block(self):
    response_lines = ["#command arg1 arg2 arg3 <<", "multi-line content", "#end"]
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg1", "arg2", "arg3"],
            multiline_content=["multi-line content"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_only_non_command_lines(self):
    response_lines = ["This is a simple text.", "Just some random words."]
    expected_commands = []
    expected_non_commands = [
        "This is a simple text.", "Just some random words."
    ]
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_interspersed_commands_and_non_commands(self):
    response_lines = ["Some intro text.", "#command1 arg1", "Middle text", "#command2", "Ending text."]
    expected_commands = [
        CommandInput(command_name="command1", arguments=["arg1"]),
        CommandInput(command_name="command2", arguments=[])
    ]
    expected_non_commands = ["Some intro text.", "Middle text", "Ending text."]
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_single_line_with_backslash_n(self):
    response_lines = ["#command arg1 arg2 <<\\nline1\\nline2\\n#end"]
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg1", "arg2"],
            multiline_content=["line1", "line2"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_no_multiline_interpretation(self):
    response_lines = ['#command arg1 "some <<\\nblah\\nblah\\n#end"']
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg1", "some <<\\nblah\\nblah\\n#end"],
        )
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_non_activation_of_mode(self):
    response_lines = ["#command <<\\nline0\\napostrophe:'\\n#end some garbage"]
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["<<\\nline0\\napostrophe:'\\n#end some garbage"],
        )
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_default_end_marker_extra_tokens(self):
    response_lines = ["#command arg.py <<", "line0", "line1", "#end (arg.py)"]
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg.py"],
            multiline_content=["line0", "line1"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_end_marker_with_valid_argument(self):
    response_lines = ["#command arg.py <<EOL", "line0", "line1", "EOL (arg.py)"]
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg.py"],
            multiline_content=["line0", "line1"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_end_marker_with_warning(self):
    response_lines = ["#command arg <<EOL", "line0", "line1", "EOL some random text"]
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg"],
            multiline_content=["line0", "line1"])
    ]
    expected_non_commands = [
        "Warning: extra tokens after EOL directive ignored: some random text"
    ]
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))

  def test_end_marker_only_with_space(self):
    response_lines = ["#command arg <<", "line0", "#endnot", "#end"]
    expected_commands = [
        CommandInput(
            command_name="command",
            arguments=["arg"],
            multiline_content=["line0", "#endnot"])
    ]
    expected_non_commands = []
    self.assertEqual(
        ExtractCommands(response_lines), (expected_commands, expected_non_commands))


if __name__ == '__main__':
  unittest.main()
