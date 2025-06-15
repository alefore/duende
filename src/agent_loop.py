import argparse
import json
import os
import sys
import openai
import logging
import re
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)
from typing import List, Dict, Optional, Tuple, Union, Pattern
from abc import ABC, abstractmethod

from select_python import SelectPythonCommand
from agent_command import AgentCommand, CommandInput
from validation import ValidationManager, CreateValidationManager
from read_file_command import ReadFileCommand
from list_files_command import ListFilesCommand
from write_file_command import WriteFileCommand
from search_file_command import SearchFileCommand
from select_commands import SelectTextCommand, SelectOverwriteCommand
from selection_manager import SelectionManager
from file_access_policy import (FileAccessPolicy, RegexFileAccessPolicy,
                                CurrentDirectoryFileAccessPolicy,
                                CompositeFileAccessPolicy)
from validate_command import ValidateCommand
from list_files import list_all_files
from parsing import ExtractCommands

logging.basicConfig(level=logging.INFO)

# Constants
CONVERSATION_KEY = 'conversation'
COMMAND_PREFIX = '#'

# Type alias for messages
Message = Union[
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
]


class ConfirmationManager(ABC):

  @abstractmethod
  def RequireConfirmation(self, message: str) -> Optional[str]:
    """Blocks execution until confirmation is given, returning additional guidance if provided by the user."""
    pass


class CLIConfirmationManager(ConfirmationManager):

  def RequireConfirmation(self, message: str) -> Optional[str]:
    print(message)
    return input(
        "Confirm operations? Enter a message to provide guidance to the AI: "
    ).strip()


class CommandRegistry:

  def __init__(self) -> None:
    self.commands: Dict[str, AgentCommand] = {}

  def Register(self, name: str, command: AgentCommand):
    self.commands[name] = command

  def Get(self, name: str) -> Optional[AgentCommand]:
    return self.commands.get(name)

  def HelpText(self) -> str:
    return '\n'.join(f"{COMMAND_PREFIX}{name}: {cmd.GetDescription()}"
                     for name, cmd in self.commands.items())


def LoadConversation(path: str) -> List[Message]:
  try:
    with open(path, 'r') as f:
      return json.load(f)[CONVERSATION_KEY]
  except FileNotFoundError:
    logging.info("Starting new conversation.")
    return []


def SaveConversation(path: str, messages: List[Message]):
  with open(path, 'w') as f:
    json.dump({CONVERSATION_KEY: messages}, f, indent=2)


def CallChatgpt(model: str, messages: List[Message]) -> Optional[str]:
  response = openai.chat.completions.create(model=model, messages=messages)
  return response.choices[0].message.content


def ParseArguments() -> argparse.Namespace:
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--api_key', type=str, default=os.path.expanduser('~/.openai/api_key'))
  parser.add_argument(
      '--task',
      type=str,
      required=True,
      help="File path for task prompt. The conversation will be stored in a corresponding .conversation.json file."
  )
  parser.add_argument(
      '--model',
      type=str,
      default='gpt-4o',
      help="The model name to use for OpenAI API requests.")
  parser.add_argument(
      '--file_access_regex',
      type=str,
      help="Regex to match allowed file paths. Defaults to allowing all paths. Match is based on relative path to current directory."
  )
  parser.add_argument(
      '--confirm',
      type=str,
      default='',
      help="Regex to match commands requiring confirmation before execution.")
  parser.add_argument(
      '--test_file_access',
      action='store_true',
      help="Test the file access policy by listing all matched files and exit.")
  parser.add_argument(
      '--confirm_done',
      action='store_true',
      help="Require confirmation before executing the done command.")
  return parser.parse_args()


def LoadOpenAIAPIKey(api_key_path: str):
  with open(api_key_path, 'r') as f:
    openai.api_key = f.read().strip()


def CreateFileAccessPolicy(args: argparse.Namespace) -> FileAccessPolicy:
  policies: List[FileAccessPolicy] = [CurrentDirectoryFileAccessPolicy()]
  if args.file_access_regex:
    policies.append(RegexFileAccessPolicy(args.file_access_regex))
  return CompositeFileAccessPolicy(policies)


def TestFileAccess(file_access_policy: FileAccessPolicy):
  for file in list_all_files('.', file_access_policy):
    print(file)


def CreateCommandRegistry(
    file_access_policy: FileAccessPolicy,
    validation_manager: Optional[ValidationManager]) -> CommandRegistry:
  registry = CommandRegistry()
  registry.Register("read_file", ReadFileCommand(file_access_policy))
  registry.Register("list_files", ListFilesCommand(file_access_policy))

  if validation_manager:
    registry.Register("validate", ValidateCommand(validation_manager))

  registry.Register("write_file",
                    WriteFileCommand(file_access_policy, validation_manager))
  registry.Register("search", SearchFileCommand(file_access_policy))

  selection_manager = SelectionManager()
  registry.Register("select",
                    SelectTextCommand(file_access_policy, selection_manager))
  registry.Register(
      "select_overwrite",
      SelectOverwriteCommand(selection_manager, validation_manager))

  if any(
      file.endswith('.py') for file in list_all_files('.', file_access_policy)):
    registry.Register(
        "select_python",
        SelectPythonCommand(file_access_policy, selection_manager))

  return registry


def LoadOrCreateConversation(
    prompt_path: str, registry: CommandRegistry) -> Tuple[List[Message], str]:
  conversation_path = re.sub(r'\.txt$', '.conversation.json', prompt_path)
  messages = LoadConversation(conversation_path)
  if not messages:
    prompt = "You are a coding assistant operating in a command loop environment. Use commands prefixed with `#`. Anything that is not a command will be ignored.\n\n"
    with open(prompt_path, 'r') as f:
      prompt += f.read() + "\n\n"
    prompt += "Some commands accept multi-line information, like this:\n\n#write_file foo.py\nline0\nline1\n…\n#end\n\n(i.e., #command_name arg0 arg1 ... << \\n multiple lines \\n #end \\n).\n\nWhen you're done (or if you get stuck), issue #done to notify the human and stop this conversation.\n\nAnything sent outside of commands will be treated as plain text.\n\nYou are encouraged to send many commands per response (not just one). For example, if you want to read 5 files, you can issue 5 #read_file commands at once."
    prompt += "\nAvailable commands:\n" + registry.HelpText()
    messages.append({'role': 'system', 'content': prompt})

  return messages, conversation_path


class AgentLoop:

  def __init__(self,
               model: str,
               messages: List[Message],
               registry: CommandRegistry,
               confirm_regex: Optional[Pattern] = None,
               confirm_done: bool = False,
               confirmation_manager: Optional[ConfirmationManager] = None):
    self.model = model
    self.messages = messages
    self.registry = registry
    self.confirm_regex = confirm_regex
    self.confirm_done = confirm_done
    self.confirmation_manager = confirmation_manager or CLIConfirmationManager()

  def run(self):
    while True:
      logging.info("Querying ChatGPT...")
      response = CallChatgpt(self.model, self.messages)
      if not response:
        logging.warning("No response from chatgpt.")
        break

      self.messages.append({'role': 'assistant', 'content': response})
      commands, non_command_lines = ExtractCommands(response)

      if non_command_lines:
        print("\nNon-command Output:\n" + "\n".join(non_command_lines) + "\n")

      if self.confirm_regex and (any(
          self.confirm_regex.match(ci.command_name) for ci in commands) or
                                 non_command_lines):
        print("\nAssistant:\n" + response + "\n")

        guidance = self.confirmation_manager.RequireConfirmation(
            "Confirm operations? Enter a message to provide guidance to the AI: "
        )

        if guidance:
          print("Your guidance will be sent to the AI.")
          self.messages.append({
              'role': 'user',
              'content': f"Message from the human operator: {guidance}"
          })

      all_output = self._execute_commands(commands, non_command_lines)

      user_feedback = '\n\n'.join(all_output)
      self.messages.append({'role': 'user', 'content': user_feedback})

  def _execute_commands(self, commands, non_command_lines):
    all_output: List[str] = []
    if not commands:
      if non_command_lines:
        all_output = non_command_lines
      else:
        all_output = [
            "Error: No commands or non-command lines found in response! "
            "Use #done if you are done with your task."
        ]
    else:
      for cmd_input in commands:
        if cmd_input.command_name == "done":
          if self.confirm_done:
            guidance = self.confirmation_manager.RequireConfirmation(
                "Confirm #done command? Enter an empty string to accept and terminate, or some message to be sent to the AI asking it to continue. "
            )
            if guidance:
              print("Your guidance will be sent to the AI.")
              self.messages.append({
                  'role': 'user',
                  'content': f"Message from the human operator: {guidance}"
              })
              continue
          return all_output

        command = self.registry.Get(cmd_input.command_name)
        if not command:
          output = f"Unknown command: {cmd_input.command_name}"
          logging.error(output)
          all_output.append(output)
          continue

        command_output = command.Execute(cmd_input)
        all_output.extend(command_output.output)
        if command_output.errors:
          all_output.extend(
              f"Error: {error}" for error in command_output.errors)
        logging.info(command_output.summary)

    return all_output


def main() -> None:
  args: argparse.Namespace = ParseArguments()

  LoadOpenAIAPIKey(args.api_key)

  file_access_policy: FileAccessPolicy = CreateFileAccessPolicy(args)

  if args.test_file_access:
    TestFileAccess(file_access_policy)
    return

  validation_manager: Optional[ValidationManager] = CreateValidationManager()
  if validation_manager:
    initial_validation_result = validation_manager.Validate()
    if initial_validation_result and initial_validation_result.returncode != 0:
      logging.error("Initial validation failed, aborting further operations.")
      return

  registry: CommandRegistry = CreateCommandRegistry(file_access_policy,
                                                    validation_manager)
  messages, conversation_path = LoadOrCreateConversation(args.task, registry)

  confirm_regex: Optional[Pattern] = re.compile(
      args.confirm) if args.confirm else None
  loop: AgentLoop = AgentLoop(args.model, messages, registry, confirm_regex,
                              args.confirm_done)
  loop.run()


if __name__ == '__main__':
  main()
