import json
import os
import sys
import openai
import logging
import re
import shlex
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)
from typing import List, Dict, Optional, Tuple, Union
from agent_command import AgentCommand, CommandInput
from notify_command import NotifyCommand
from read_file_command import ReadFileCommand
from list_files_command import ListFilesCommand
from write_file_command import WriteFileCommand
from search_file_command import SearchFileCommand  # Import the new command
from select_commands import SelectTextCommand, SelectOverwriteCommand
from file_access_policy import (FileAccessPolicy, RegexFileAccessPolicy,
                                CurrentDirectoryFileAccessPolicy,
                                CompositeFileAccessPolicy)
from list_files import list_all_files
from parsing import ExtractCommands  # Importing the ExtractCommands from parsing.py

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


def CallChatgpt(model: str, messages: List[Message]) -> str | None:
  response = openai.chat.completions.create(model=model, messages=messages)
  return response.choices[0].message.content


def main() -> None:
  import argparse

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
  args = parser.parse_args()

  # Load API key
  with open(args.api_key, 'r') as f:
    openai.api_key = f.read().strip()

  policies: List[FileAccessPolicy] = [CurrentDirectoryFileAccessPolicy()]
  if args.file_access_regex:
    policies.append(RegexFileAccessPolicy(args.file_access_regex))
  file_access_policy = CompositeFileAccessPolicy(policies)

  if args.test_file_access:
    for file in list_all_files('.', file_access_policy):
      print(file)
    return

  prompt_path = args.task
  conversation_path = re.sub(r'\.txt$', '.conversation.json', prompt_path)

  registry = CommandRegistry()
  registry.Register("notify", NotifyCommand())
  registry.Register("read_file", ReadFileCommand(file_access_policy))
  registry.Register("list_files", ListFilesCommand(file_access_policy))
  registry.Register("write_file", WriteFileCommand(file_access_policy))
  registry.Register("search", SearchFileCommand(file_access_policy))
  registry.Register("select", SelectTextCommand(file_access_policy))
  registry.Register("select_overwrite", SelectOverwriteCommand())

  messages = LoadConversation(conversation_path)
  if not messages:
    prompt = "You are a coding assistant operating in a command loop environment. Use commands prefixed with `#`. Anything that is not a command will be ignored.\n\n"
    with open(prompt_path, 'r') as f:
      prompt += f.read() + "\n\n"
    prompt += "To send multi-line arguments, use a command followed by `<<` (e.g., #notify <<`) followed by multiple lines of text, ending with a line `#end`.\nWhen you're done (or if you get stuck), issue #done to notify the human and stop this conversation.\nAny information that you send outside of commands will be ignored (use #notify to reach the human!).\nYou can send many commands per response (not just one)."
    prompt += "\nAvailable commands:\n" + registry.HelpText()
    messages.append({'role': 'system', 'content': prompt})

  # Compile the confirmation regex if provided
  confirm_regex = re.compile(args.confirm) if args.confirm else None

  # Main loop
  while True:
    logging.info("Querying ChatGPT...")
    response = CallChatgpt(args.model, messages)
    if not response:
      logging.warning("No response from chatgpt.")
      break

    messages.append({'role': 'assistant', 'content': response})

    commands = ExtractCommands(response)

    if confirm_regex and any(
        confirm_regex.match(ci.command_name) for ci in commands):
      print("\nAssistant:\n" + response + "\n")

      guidance = input(
          "Confirm operations? Enter a message to provide guidance to the AI: "
      ).strip()

      if guidance:
        print("Your guidance will be sent to the AI.")
        messages.append({
            'role': 'user',
            'content': f"Message from the human operator: {guidance}"
        })

    all_output: List[str] = []
    if not commands:
      all_output = [
          "Error: No commands found in response! "
          "Did you mean to use #notify? "
          "Use #done if you are done with your task."
      ]
    else:
      for cmd_input in commands:
        if cmd_input.command_name == "done":
          if args.confirm_done:
            guidance = input(
                "Confirm #done command? Enter an empty string to accept and terminate, or some message to be sent to the AI asking it to continue."
            ).strip()
            if guidance:
              print("Your guidance will be sent to the AI.")
              messages.append({
                  'role': 'user',
                  'content': f"Message from the human operator: {guidance}"
              })
              continue
          logging.info("Received #done. Stopping.")
          SaveConversation(conversation_path, messages)
          return

        command = registry.Get(cmd_input.command_name)
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

    user_feedback = '\n\n'.join(all_output)
    messages.append({'role': 'user', 'content': user_feedback})
    SaveConversation(conversation_path, messages)


if __name__ == '__main__':
  main()
