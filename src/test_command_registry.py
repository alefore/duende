import unittest
from unittest.mock import Mock, patch

from agent_command import (AgentCommand, CommandInput, CommandOutput,
                           CommandSyntax)
from command_registry import (CommandRegistrationError, CommandRegistry,
                              UnknownCommandError)
from conversation import MultilineContent


class FakeCommand(AgentCommand):
  """A mock AgentCommand for testing purposes."""

  def __init__(self, name: str, aliases: list[str] | None = None):
    self._name = name
    self._aliases = aliases or []

  def Name(self) -> str:
    return self._name

  def Aliases(self) -> list[str]:
    return self._aliases

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(description="A fake command for testing.")


class CommandRegistryTest(unittest.TestCase):

  def setUp(self) -> None:
    self.registry = CommandRegistry()

  def test_register_and_get_command(self) -> None:
    cmd = FakeCommand("test_command")
    self.registry.Register(cmd)
    self.assertIs(self.registry.Get("test_command"), cmd)

  def test_get_non_existent_command(self) -> None:
    self.assertIsNone(self.registry.Get("non_existent"))

    self.registry.Register(FakeCommand("real_command"))
    self.assertIsNone(self.registry.Get("another_non_existent"))

  def test_register_command_with_aliases(self) -> None:
    cmd = FakeCommand("test_command", ["t", "tc"])
    self.registry.Register(cmd)
    self.assertIs(self.registry.Get("test_command"), cmd)
    self.assertIs(self.registry.Get("t"), cmd)
    self.assertIs(self.registry.Get("tc"), cmd)

  def test_register_clash_with_canonical_name(self) -> None:
    self.registry.Register(FakeCommand("command1"))
    with self.assertRaisesRegex(CommandRegistrationError,
                                "Name/alias clash for: command1"):
      self.registry.Register(FakeCommand("command1"))

  def test_register_clash_with_alias(self) -> None:
    self.registry.Register(FakeCommand("command1", ["c1"]))
    with self.assertRaisesRegex(CommandRegistrationError,
                                "Name/alias clash for: c1"):
      self.registry.Register(FakeCommand("c1"))

  def test_register_alias_clash_with_canonical_name(self) -> None:
    self.registry.Register(FakeCommand("command1"))
    with self.assertRaisesRegex(CommandRegistrationError,
                                "Name/alias clash for: command1"):
      self.registry.Register(FakeCommand("command2", ["command1"]))

  def test_register_alias_clash_with_alias(self) -> None:
    self.registry.Register(FakeCommand("command1", ["c1"]))
    with self.assertRaisesRegex(CommandRegistrationError,
                                "Name/alias clash for: c1"):
      self.registry.Register(FakeCommand("command2", ["c1"]))

  def test_register_multiple_clashes_error_message(self) -> None:
    self.registry.Register(FakeCommand("command1", ["a", "b"]))
    with self.assertRaisesRegex(CommandRegistrationError,
                                "Name/alias clash for: a, b"):
      self.registry.Register(FakeCommand("command2", ["b", "a"]))

  def test_list_all_empty(self) -> None:
    self.assertEqual(self.registry.list_all(), [])

  def test_list_all_returns_sorted_canonical_names(self) -> None:
    self.registry.Register(FakeCommand("zebra", ["z"]))
    self.registry.Register(FakeCommand("apple", ["a"]))
    self.assertEqual(self.registry.list_all(), ["apple", "zebra"])

  @patch('command_registry.FormatHelp')
  def test_help_text_empty(self, mock_format_help: Mock) -> None:
    mock_return = MultilineContent("empty")
    mock_format_help.return_value = mock_return
    self.assertIs(self.registry.HelpText(), mock_return)
    mock_format_help.assert_called_once_with([])

  @patch('command_registry.FormatHelp')
  def test_help_text_with_commands_sorted(self, mock_format_help: Mock) -> None:
    cmd_apple = FakeCommand("apple")
    cmd_zebra = FakeCommand("zebra")
    self.registry.Register(cmd_zebra)
    self.registry.Register(cmd_apple)

    mock_return = MultilineContent("help text")
    mock_format_help.return_value = mock_return
    self.assertIs(self.registry.HelpText(), mock_return)

    mock_format_help.assert_called_once()
    called_with_commands = mock_format_help.call_args[0][0]
    self.assertEqual(len(called_with_commands), 2)
    self.assertIs(called_with_commands[0], cmd_apple)
    self.assertIs(called_with_commands[1], cmd_zebra)


class UnknownCommandErrorTest(unittest.TestCase):

  def test_unknown_command_error_message(self) -> None:
    err = UnknownCommandError(["b", "a", "c"])
    self.assertEqual(err.unknown_commands, ["b", "a", "c"])
    self.assertEqual(str(err), "Unknown command(s): a, b, c")
