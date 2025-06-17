import json
import openai
import logging
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)
from typing import List, Optional, Tuple, Union, Pattern, NamedTuple
from validation import ValidationManager

from confirmation import ConfirmationState
from command_registry import CommandRegistry, CreateCommandRegistry
from agent_command import CommandInput
from file_access_policy import (FileAccessPolicy, RegexFileAccessPolicy,
                                CurrentDirectoryFileAccessPolicy,
                                CompositeFileAccessPolicy)
from list_files import list_all_files
from parsing import ExtractCommands

logging.basicConfig(level=logging.INFO)

# Constants
CONVERSATION_KEY = 'conversation'

# Type alias for messages
Message = Union[
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
]


class AgentLoopOptions(NamedTuple):
  conversation_path: str
  model: str
  messages: List[Message]
  commands_registry: CommandRegistry
  confirmation_state: ConfirmationState
  confirm_regex: Optional[Pattern] = None
  confirm_done: bool = False
  always_validate: bool = True
  validation_manager: Optional[ValidationManager] = None


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


def LoadOpenAIAPIKey(api_key_path: str):
  with open(api_key_path, 'r') as f:
    openai.api_key = f.read().strip()


class AgentLoop:

  def __init__(self, options: AgentLoopOptions):
    self.options = options

  def run(self) -> None:
    while True:
      logging.info("Querying ChatGPT...")
      response = CallChatgpt(self.options.model, self.options.messages)
      if not response:
        logging.warning("No response from chatgpt.")
        break

      SaveConversation(self.options.conversation_path, self.options.messages)
      self.options.messages.append({'role': 'assistant', 'content': response})
      commands, non_command_lines = ExtractCommands(response)

      messages_for_ai: List[str] = []

      if (self.options.confirm_regex and any(
          self.options.confirm_regex.match(ci.command_name)
          for ci in commands)) or non_command_lines:
        guidance = self.options.confirmation_state.RequireConfirmation(response)
        if guidance:
          print("Your guidance will be sent to the AI.")
          messages_for_ai.append(f"Message from human: {guidance}")

      self.options.confirmation_state.RegisterInteraction()
      messages_for_ai.extend(self._execute_commands(commands))

      if self.options.always_validate:
        assert self.options.validation_manager
        validation_result = self.options.validation_manager.Validate()
        if validation_result.returncode != 0:
          logging.info(f"Validation failed: {validation_result.returncode}")
          messages_for_ai.append(
              "The validation command is currently reporting failures "
              "(normal if you are in the middle applying changes). "
              "To see the failures, use: #validate")

      self.options.messages.append({
          'role': 'user',
          'content': '\n'.join(messages_for_ai)
      })

  def _execute_commands(self, commands) -> List[str]:
    all_output: List[str] = []
    if not commands:
      all_output = [
          "Error: No commands found in response! "
          "Use #done if you are done with your task."
      ]
    else:
      for cmd_input in commands:
        if cmd_input.command_name == "done":
          if self.options.confirm_done:
            guidance = self.options.confirmation_state.RequireConfirmation(
                "Confirm #done command? Enter an empty string to accept and terminate, or some message to be sent to the AI asking it to continue. "
            )
            if guidance:
              print("Your guidance will be sent to the AI.")
              self.options.messages.append({
                  'role': 'user',
                  'content': f"Message from the human operator: {guidance}"
              })
              continue
          return all_output

        command = self.options.commands_registry.Get(cmd_input.command_name)
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
