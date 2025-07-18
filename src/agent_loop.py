import json
import logging
from conversation import Conversation, ConversationFactory
from message import Message, ContentSection
from conversation_state import ConversationState
from typing import cast, Generator, List, Optional, Tuple, Union

from validation import ValidationManager
from agent_command import CommandInput
from agent_command import CommandOutput
from agent_loop_options import AgentLoopOptions
from command_registry import CommandRegistry
from command_registry_factory import CreateCommandRegistry
from confirmation import ConfirmationState
from conversational_ai import ConversationalAI
from file_access_policy import FileAccessPolicy
from validate_command_input import ValidateCommandInput

logging.basicConfig(level=logging.INFO)


class CommandValidationError(Exception):
  pass


class AgentLoop:

  def __init__(self, options: AgentLoopOptions):
    self.options = options
    self.conversation = self.options.conversation
    self.ai_conversation = options.conversational_ai.StartConversation(
        self.conversation)
    self._previous_validation_passed = True
    self.next_message: Optional[Message] = self.options.start_message

  def _validate_command(self, cmd_input: CommandInput) -> None:
    command = self.options.commands_registry.Get(cmd_input.command_name)
    if not command:
      error_msg = f"Error: Unknown command: {cmd_input.command_name}"
      logging.error(error_msg)
      raise CommandValidationError(error_msg)

    warnings = ValidateCommandInput(command.Syntax(), cmd_input,
                                    self.options.file_access_policy)
    if warnings:
      logging.info(f"Warnings: {','.join(warnings)}")
      raise CommandValidationError("\n".join([
          f"Warning {cmd_input.command_name}: {warning}" for warning in warnings
      ]))

  def _process_ai_response(self,
                           response_message: Message) -> Optional[Message]:
    commands: List[CommandInput] = []
    non_command_lines: List[str] = []

    self.conversation.SetState(ConversationState.PARSING_COMMANDS)

    next_message = Message(role='user')

    for section in response_message.GetContentSections():
      if section.command:
        cmd_input = section.command
        try:
          self._validate_command(cmd_input)
        except CommandValidationError as e:
          non_command_lines.append(f"Invalid command invocation: {str(e)}")
          next_message.PushSection(
              ContentSection(
                  content=str(e),
                  summary=f"Validation warnings: '{cmd_input.command_name}'"))
        else:
          commands.append(cmd_input)
      else:
        non_command_lines.append(section.content)

    has_human_guidance = False
    if (self.options.confirm_regex and any(
        self.options.confirm_regex.match(ci.command_name)
        for ci in commands)) or non_command_lines:
      has_human_guidance = self._get_human_guidance(
          prompt="Accept input?",
          summary="Human guidance for AI",
          content_prefix="Message from human",
          next_message=next_message)

    self.options.confirmation_state.RegisterInteraction(
        self.conversation.GetId())

    self.conversation.SetState(ConversationState.RUNNING_COMMANDS)
    command_outputs, done_command_received = self._execute_commands(commands)
    for content_section in command_outputs:
      next_message.PushSection(content_section)

    if done_command_received and not has_human_guidance:
      return None

    if not self.options.skip_implicit_validation:
      self.conversation.SetState(
          ConversationState.EXECUTING_IMPLICIT_VALIDATION)
      assert self.options.validation_manager
      validation_result = self.options.validation_manager.Validate()
      if not validation_result.success:
        if self._previous_validation_passed:
          logging.info(f"Validation failed: {validation_result.error}")
          next_message.PushSection(
              ContentSection(
                  content=(
                      "The validation command is currently reporting failures "
                      "(normal if you are in the middle of applying changes). "
                      "To see the failures, use: `validate`"),
                  summary="Validation status (failures detected)"))
        self._previous_validation_passed = False
      else:
        if not self._previous_validation_passed:
          logging.info("Validation passed.")
          next_message.PushSection(
              ContentSection(
                  content="The validation command is now passing.",
                  summary="Validation status (passed)"))
        self._previous_validation_passed = True

    if not next_message.GetContentSections():
      next_message.PushSection(
          ContentSection(
              content=("Response is empty. " +
                       "The following commands are available:" +
                       ', '.join(self.options.commands_registry.list_all())),
              summary="Empty response placeholder."))
    return next_message

  def set_next_message(self, message: Message) -> None:
    self.next_message = message

  def run(self) -> None:
    logging.info("Starting AgentLoop run method...")
    next_message: Optional[Message] = self.next_message
    self.next_message = None

    while next_message:
      logging.info("Querying AI...")
      self.conversation.SetState(ConversationState.WAITING_FOR_AI_RESPONSE)
      next_message = self._process_ai_response(
          self.ai_conversation.SendMessage(next_message))
    self.conversation.SetState(ConversationState.DONE)

  def _get_human_guidance(self, prompt: str, summary: str, content_prefix: str,
                          next_message: Message) -> bool:
    self.conversation.SetState(ConversationState.WAITING_FOR_CONFIRMATION)
    guidance = self.options.confirmation_state.RequireConfirmation(
        self.conversation.GetId(), prompt)
    if not guidance:
      logging.info("No guidance.")
      return False

    logging.info("Your guidance will be sent to the AI.")
    next_message.PushSection(
        ContentSection(
            content=f"{content_prefix}: {guidance}", summary=summary))
    return True

  def _execute_one_command(self,
                           cmd_input: CommandInput) -> List[ContentSection]:
    command_name = cmd_input.command_name
    command = self.options.commands_registry.Get(command_name)
    assert command
    command_output = command.run(cmd_input.args)

    outputs: List[ContentSection] = []
    if command_output.output:
      outputs.append(
          # We deliberately leave `content` empty (since the output is included
          # in `command_output`, so this would make it redundant).
          ContentSection(
              content='',
              command_output=command_output,
              summary=command_output.summary or
              f"Output for command '{command_name}'"))
    if command_output.errors:
      outputs.append(
          ContentSection(
              content=f"Error: {command_output.errors}",
              command_output=command_output,
              summary=f"Errors for command '{command_name}'"))
    if not command_output.output and not command_output.errors and command_output.task_done:
      outputs.append(
          ContentSection(
              content="",
              command_output=command_output,
              summary=command_output.summary))

    logging.info(command_output.summary)
    return outputs

  # Return value indicates whether `done` was received.
  def _execute_commands(
      self, commands: List[CommandInput]) -> Tuple[List[ContentSection], bool]:
    outputs: List[ContentSection] = []
    for cmd_input in commands:
      outputs.extend(self._execute_one_command(cmd_input))

    return outputs, any(
        o.command_output and o.command_output.task_done for o in outputs)
