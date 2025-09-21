import unittest
from unittest.mock import MagicMock
import asyncio

from agent_command import CommandInput
from shell_command_command import ShellCommandCommand


class TestShellCommandCommand(unittest.IsolatedAsyncioTestCase):

  async def asyncSetUp(self):
    self.shell_command = ShellCommandCommand()

  async def test_shell_command_success(self):
    command_input = CommandInput(name="shell_command", arguments={'command': 'echo hello'})
    output = await self.shell_command.run(command_input.arguments)

    self.assertEqual(output.errors, "")
    self.assertEqual(output.summary, "Shell command executed with exit status 0.")
    self.assertIn("'stdout': 'hello'", output.output)
    self.assertIn("'stderr': ''", output.output)
    self.assertIn("'exit_status': 0", output.output)

  async def test_shell_command_failure(self):
    command_input = CommandInput(name="shell_command", arguments={'command': 'false'})
    output = await self.shell_command.run(command_input.arguments)

    self.assertEqual(output.errors, "")
    self.assertEqual(output.summary, "Shell command executed with exit status 1.")
    self.assertIn("'stdout': ''", output.output)
    self.assertIn("'stderr': ''", output.output)
    self.assertIn("'exit_status': 1", output.output)

  async def test_shell_command_stderr(self):
    command_input = CommandInput(name="shell_command", arguments={'command': '>&2 echo error_message'})
    output = await self.shell_command.run(command_input.arguments)

    self.assertIn("error_message", output.errors)
    self.assertEqual(output.summary, "Shell command executed with exit status 0. Stderr not empty.")
    self.assertIn("'stdout': ''", output.output)
    self.assertIn("'stderr': 'error_message'", output.output)
    self.assertIn("'exit_status': 0", output.output)

  async def test_shell_command_non_existent_command(self):
    command_input = CommandInput(name="shell_command", arguments={'command': 'non_existent_command_12345'})
    output = await self.shell_command.run(command_input.arguments)

    self.assertNotEqual(output.errors, "")
    self.assertIn("Shell command executed with exit status", output.summary)
    self.assertIn("'stdout': ''", output.output)
    self.assertIn("'stderr': ", output.output)
    self.assertNotEqual(output.output.find("'exit_status': ") + len("'exit_status': "), len(output.output)-1) # Check if exit_status is present and not at the end

