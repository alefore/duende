import unittest
from parsing import ExtractCommands
from agent_command import CommandInput


class TestExtractCommands(unittest.TestCase):

  def test_single_line_command_without_arguments(self):
    self.assertEqual(
        ExtractCommands(["#command"]),
        ([CommandInput(command_name="command", arguments=[])], []))

  def test_single_line_command_with_arguments(self):
    self.assertEqual(
        ExtractCommands(["#command arg1 arg2"]),
        ([CommandInput(command_name="command", arguments=["arg1", "arg2"])
         ], []))

  def test_multiline_command(self):
    self.assertEqual(
        ExtractCommands(["#command arg1 <<", "line1", "line2", "#end"]), ([
            CommandInput(
                command_name="command",
                arguments=["arg1"],
                multiline_content=["line1", "line2"])
        ], []))

  def test_multiline_command_with_empty_lines(self):
    self.assertEqual(
        ExtractCommands(["#command arg1 <<", "foo", "", "bar", "#end"]), ([
            CommandInput(
                command_name="command",
                arguments=["arg1"],
                multiline_content=["foo", "", "bar"])
        ], []))

  def test_multiline_command_with_eof_marker(self):
    self.assertEqual(
        ExtractCommands(["#command arg1 <<EOF", "line1", "line2", "EOF"]), ([
            CommandInput(
                command_name="command",
                arguments=["arg1"],
                multiline_content=["line1", "line2"])
        ], []))

  def test_multiline_command_with_custom_marker(self):
    self.assertEqual(
        ExtractCommands(["#command arg1 <<CUSTOM", "line1", "CUSTOM"]), ([
            CommandInput(
                command_name="command",
                arguments=["arg1"],
                multiline_content=["line1"])
        ], []))

  def test_multiple_commands_with_various_markers(self):
    self.assertEqual(
        ExtractCommands([
            "#command1 arg1 <<EOF", "line1", "EOF", "#command2 <<END", "line2",
            "END"
        ]), ([
            CommandInput(
                command_name="command1",
                arguments=["arg1"],
                multiline_content=["line1"]),
            CommandInput(
                command_name="command2",
                arguments=[],
                multiline_content=["line2"])
        ], []))

  def test_multiple_commands(self):
    self.assertEqual(
        ExtractCommands([
            "#command1 arg1", "#command2 arg2 <<", "line1", "#end", "#command3"
        ]), ([
            CommandInput(command_name="command1", arguments=["arg1"]),
            CommandInput(
                command_name="command2",
                arguments=["arg2"],
                multiline_content=["line1"]),
            CommandInput(command_name="command3", arguments=[])
        ], []))

  def test_command_with_special_characters_using_shlex(self):
    self.assertEqual(
        ExtractCommands(['#command "arg1 with spaces" arg2']), ([
            CommandInput(
                command_name="command", arguments=["arg1 with spaces", "arg2"])
        ], []))

  def test_invalid_shlex_argument_handling(self):
    self.assertEqual(
        ExtractCommands(["#command 'unterminated quote"]), ([
            CommandInput(
                command_name="command", arguments=["'unterminated quote"])
        ], []))

  def test_commands_with_random_non_command_text_in_between(self):
    self.assertEqual(
        ExtractCommands([
            "Random text not a command", "#command1 arg1", "More random text",
            "#command2 arg2"
        ]), ([
            CommandInput(command_name="command1", arguments=["arg1"]),
            CommandInput(command_name="command2", arguments=["arg2"])
        ], ["Random text not a command", "More random text"]))

  def test_command_with_multiple_arguments_begin_multiline_block(self):
    self.assertEqual(
        ExtractCommands(
            ["#command arg1 arg2 arg3 <<", "multi-line content", "#end"]), ([
                CommandInput(
                    command_name="command",
                    arguments=["arg1", "arg2", "arg3"],
                    multiline_content=["multi-line content"])
            ], []))

  def test_only_non_command_lines(self):
    self.assertEqual(
        ExtractCommands(["This is a simple text.", "Just some random words."]),
        ([], ["This is a simple text.", "Just some random words."]))

  def test_interspersed_commands_and_non_commands(self):
    self.assertEqual(
        ExtractCommands([
            "Some intro text.", "#command1 arg1", "Middle text", "#command2",
            "Ending text."
        ]), ([
            CommandInput(command_name="command1", arguments=["arg1"]),
            CommandInput(command_name="command2", arguments=[])
        ], ["Some intro text.", "Middle text", "Ending text."]))

  def test_single_line_with_backslash_n(self):
    self.assertEqual(
        ExtractCommands(["#command arg1 arg2 <<\\nline1\\nline2\\n#end"]), ([
            CommandInput(
                command_name="command",
                arguments=["arg1", "arg2"],
                multiline_content=["line1", "line2"])
        ], []))

  def test_no_multiline_interpretation(self):
    self.assertEqual(
        ExtractCommands(['#command arg1 "some <<\\nblah\\nblah\\n#end"']), ([
            CommandInput(
                command_name="command",
                arguments=["arg1", "some <<\\nblah\\nblah\\n#end"],
            )
        ], []))

  def test_non_activation_of_mode(self):
    self.assertEqual(
        ExtractCommands(
            ["#command <<\\nline0\\napostrophe:'\\n#end some garbage"]), ([
                CommandInput(
                    command_name="command",
                    arguments=["<<\\nline0\\napostrophe:'\\n#end some garbage"],
                )
            ], []))

  def test_default_end_marker_extra_tokens(self):
    self.assertEqual(
        ExtractCommands(
            ["#command arg.py <<", "line0", "line1", "#end (arg.py)"]), ([
                CommandInput(
                    command_name="command",
                    arguments=["arg.py"],
                    multiline_content=["line0", "line1"])
            ], []))

  def test_end_marker_with_valid_argument(self):
    self.assertEqual(
        ExtractCommands(
            ["#command arg.py <<EOL", "line0", "line1", "EOL (arg.py)"]), ([
                CommandInput(
                    command_name="command",
                    arguments=["arg.py"],
                    multiline_content=["line0", "line1"])
            ], []))

  def test_end_marker_with_warning(self):
    self.assertEqual(
        ExtractCommands(
            ["#command arg <<EOL", "line0", "line1", "EOL some random text"]),
        ([
            CommandInput(
                command_name="command",
                arguments=["arg"],
                multiline_content=["line0", "line1"])
        ], [
            "Warning: extra tokens after EOL directive ignored: some random text"
        ]))

  def test_end_marker_only_with_space(self):
    self.assertEqual(
        ExtractCommands(["#command arg <<", "line0", "#endnot", "#end"]), ([
            CommandInput(
                command_name="command",
                arguments=["arg"],
                multiline_content=["line0", "#endnot"])
        ], []))


if __name__ == '__main__':
  unittest.main()
