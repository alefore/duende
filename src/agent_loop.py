import json
import openai
import logging
from conversation import Conversation, Message
from typing import cast, Generator, List, Optional, Tuple, Union, Pattern, NamedTuple
from validation import ValidationManager

from confirmation import ConfirmationState
from command_registry import CommandRegistry
from agent_command import CommandInput
from file_access_policy import FileAccessPolicy
from list_files import list_all_files
from parsing import ExtractCommands
from validate_command_input import ValidateCommandInput
from conversational_ai import ConversationalAI

logging.basicConfig(level=logging.INFO)

# Constants
CONVERSATION_KEY = 'conversation'


class AgentLoopOptions(NamedTuple):
  conversation_path: str
  model: str
  conversation: Conversation
  start_message: Message
  commands_registry: CommandRegistry
  confirmation_state: ConfirmationState
  file_access_policy: FileAccessPolicy
  conversational_ai: ConversationalAI
  confirm_regex: Optional[Pattern] = None
  confirm_done: bool = False
  skip_implicit_validation: bool = False
  validation_manager: Optional[ValidationManager] = None


class AgentLoop:

  def __init__(self, options: AgentLoopOptions):
    self.options = options
    self.conversation = self.options.conversation
    self.ai_conversation = options.conversational_ai.StartConversation(
        self.conversation)

  def run(self) -> None:
    next_message: Message = self.options.start_message
    while True:
      logging.info("Querying ChatGPT...")
      response_message: Message = self.ai_conversation.SendMessage(next_message)
      self.conversation.Save(self.options.conversation_path)

      commands, non_command_lines = ExtractCommands(response_message.content)

      messages_for_ai: List[str] = []

      if (self.options.confirm_regex and any(
          self.options.confirm_regex.match(ci.command_name)
          for ci in commands)) or non_command_lines:
        guidance = self.options.confirmation_state.RequireConfirmation(
            response_message.content)
        if guidance:
          print("Your guidance will be sent to the AI.")
          messages_for_ai.append(f"Message from human: {guidance}")

      self.options.confirmation_state.RegisterInteraction()
      messages_for_ai.extend(self._execute_commands(commands))

      if not self.options.skip_implicit_validation:
        assert self.options.validation_manager
        validation_result = self.options.validation_manager.Validate()
        if validation_result.returncode != 0:
          logging.info(f"Validation failed: {validation_result.returncode}")
          messages_for_ai.append(
              "The validation command is currently reporting failures "
              "(normal if you are in the middle of applying changes). "
              "To see the failures, use: #validate")

      next_message = Message(role='user', content='\n'.join(messages_for_ai))

  def _execute_commands(self, commands) -> Generator[str, None, None]:
    if not commands:
      yield "Error: No commands found in response! Use #done if you are done with your task."
      return

    for cmd_input in commands:
      if cmd_input.command_name == "done":
        if self.options.confirm_done:
          guidance = self.options.confirmation_state.RequireConfirmation(
              "Confirm #done command? Enter an empty string to accept and terminate, or some message to be sent to the AI asking it to continue."
          )
          if guidance:
            logging.info("Your guidance will be sent to the AI.")
            yield f"Notice from human: {guidance}"
            continue
        return

      command = self.options.commands_registry.Get(cmd_input.command_name)
      if not command:
        output = f"Unknown command: {cmd_input.command_name}"
        logging.error(output)
        yield output
        continue

      warnings = ValidateCommandInput(command.Syntax(), cmd_input,
                                      self.options.file_access_policy)
      if warnings:
        for warning in warnings:
          yield f"Warning {cmd_input.command_name}: {warning}"
        continue

      command_output = command.Execute(cmd_input)
      yield from command_output.output
      if command_output.errors:
        for error in command_output.errors:
          yield f"Error: {error}"
      logging.info(command_output.summary)
