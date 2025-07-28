import unittest
from unittest.mock import MagicMock

from agent_command import CommandInput
from command_registry_factory import create_command_registry
from file_access_policy import RegexFileAccessPolicy


class TestHelpCommand(unittest.TestCase):

  async def setUp(self):
    self.registry = await create_command_registry(
        file_access_policy=RegexFileAccessPolicy('.*'),
        validation_manager=None,
        start_new_task=MagicMock(),
        can_write=True,
        can_start_tasks=True,
        git_dirty_accept=True,
        shell_command_execution=False)
    self.help_command = self.registry.Get("help")
    self.assertIsNotNone(self.help_command)

  def test_HelpEmpty(self):
    """An empty #help invocation."""
    command_input = CommandInput('help', arguments=[])
    result = self.help_command.Execute(command_input)
    self.assertEqual(result.errors, [])
    self.assertIn("Help for:", result.summary)
    self.assertIn("select_python", result.summary)
    output_str = '\n'.join(result.output)
    self.assertIn("#help [command…]", output_str)
    #self.assertIn("#read_file path", output_str)
    self.assertIn("#list_files [directory…]", output_str)

  def test_HelpSingleValidCommand(self):
    """A #help invocation with a single existing (valid) command."""
    command_input = CommandInput('help', arguments=['read_file'])
    result = self.help_command.Execute(command_input)

    self.assertEqual(result.errors, [])
    self.assertEqual(result.summary, "Help for: read_file.")
    # self.assertIn("#read_file path", result.output[0])
    output_str = '\n'.join(result.output)
    self.assertNotIn("#help", output_str)
    self.assertNotIn("#list_files", output_str)

  def test_HelpThreeValidCommands(self):
    """A #help invocation with three existing (valid) commands."""
    command_input = CommandInput(
        'help', arguments=['read_file', 'help', 'list_files'])
    result = self.help_command.Execute(command_input)

    self.assertEqual(result.errors, [])
    self.assertEqual(result.summary, "Help for: help, list_files, read_file.")
    output_str = '\n'.join(result.output)
    # self.assertIn("#read_file path", output_str)
    self.assertIn("#help [command…]", output_str)
    self.assertIn("#list_files [directory…]", output_str)
    # Check order.
    self.assertLess(output_str.find("#help"), output_str.find("#list_files"))
    #self.assertLess(
    #    output_str.find("#list_files"), output_str.find("#read_file"))

  def test_HelpRepeatedCommands(self):
    """A #help invocation with two commands, one repeated five times."""
    args = ['read_file'] * 5 + ['help']
    command_input = CommandInput('help', arguments=args)
    result = self.help_command.Execute(command_input)

    self.assertEqual(result.errors, [])
    self.assertEqual(result.summary, "Help for: help, read_file.")
    output_str = '\n'.join(result.output)
    # self.assertIn("#read_file path", output_str)
    self.assertIn("#help [command…]", output_str)
    # self.assertEqual(output_str.count("#read_file"), 1)
    self.assertEqual(output_str.count("#help"), 1)

  def test_HelpSingleInvalidCommand(self):
    """A #help invocation with a single invalid command."""
    command_input = CommandInput('help', arguments=['non_existent_command'])
    result = self.help_command.Execute(command_input)

    self.assertEqual(len(result.errors), 1)
    self.assertEqual(result.errors[0],
                     "#help: Unknown command(s): non_existent_command")
    self.assertEqual(result.output, [])
    self.assertEqual(result.summary,
                     "Unknown command(s): non_existent_command.")

  def test_HelpMixedValidInvalidCommands(self):
    """A #help invocation with 3 valid and 2 invalid commands."""
    args = ['read_file', 'invalid1', 'help', 'list_files', 'invalid2']
    command_input = CommandInput('help', arguments=args)
    result = self.help_command.Execute(command_input)

    self.assertEqual(len(result.errors), 1)
    self.assertEqual(result.errors[0],
                     "#help: Unknown command(s): invalid1, invalid2")

    self.assertEqual(
        result.summary,
        "Help for: help, list_files, read_file. Unknown command(s): invalid1, invalid2."
    )

    output_str = '\n'.join(result.output)
    # self.assertIn("#read_file path", output_str)
    self.assertIn("#help [command…]", output_str)
    self.assertIn("#list_files [directory…]", output_str)
    self.assertNotIn("invalid1", output_str)
    self.assertNotIn("invalid2", output_str)


if __name__ == '__main__':
  unittest.main()
