import json
import logging
from conversation import Conversation, ConversationFactory
from message import Message, ContentSection
from conversation_state import ConversationState
from typing import cast, Generator, Tuple, Union

from validation import ValidationManager
from agent_command import CommandInput, CommandOutput, VariableMap
from agent_loop_options import AgentLoopOptions, BaseAgentLoop, BaseAgentLoopFactory
from confirmation import ConfirmationState
from conversational_ai import ConversationalAI
from file_access_policy import FileAccessPolicy
from validate_command_input import CommandValidationError, validate_command_input

logging.basicConfig(level=logging.INFO)


class AgentLoop(BaseAgentLoop):

  def __init__(self, options: AgentLoopOptions):
    self.options = options
    self.conversation = self.options.conversation
    self.ai_conversation = options.conversational_ai.StartConversation(
        self.conversation)
    self._previous_validation_passed = True
    self.next_message: Message | None = self.options.start_message

  async def _process_ai_response(self,
                                 response_message: Message) -> Message | None:
    commands: list[CommandInput] = []
    non_command_lines: list[str] = []

    await self.conversation.SetState(ConversationState.PARSING_COMMANDS)

    next_message = Message(role='user')

    for section in response_message.GetContentSections():
      if section.command:
        cmd_input = section.command
        try:
          cmd_input = cmd_input._replace(
              args=validate_command_input(cmd_input,
                                          self.options.commands_registry,
                                          self.options.file_access_policy))
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
      has_human_guidance = await self._get_human_guidance(
          prompt="Accept input?",
          summary="Human guidance for AI",
          content_prefix="Message from human",
          next_message=next_message)

    await self.options.confirmation_state.RegisterInteraction(
        self.conversation.GetId())

    await self.conversation.SetState(ConversationState.RUNNING_COMMANDS)
    command_outputs, done_command_output = await self._execute_commands(commands
                                                                       )
    for content_section in command_outputs:
      next_message.PushSection(content_section)

    if done_command_output and not has_human_guidance:
      await self.conversation.AddMessage(
          Message(
              role="user",
              content_sections=[
                  ContentSection(
                      content='', command_output=done_command_output)
              ]))
      return None

    if not self.options.skip_implicit_validation:
      await self.conversation.SetState(
          ConversationState.EXECUTING_IMPLICIT_VALIDATION)
      assert self.options.validation_manager
      validation_result = await self.options.validation_manager.Validate()
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
              content=("Response did not call any functions. " +
                       self.options.commands_registry.available_commands_str()),
              summary="Empty response placeholder."))
    return next_message

  def set_next_message(self, message: Message) -> None:
    self.next_message = message

  async def run(self) -> VariableMap:
    logging.info("Starting AgentLoop run method...")
    next_message: Message | None = self.next_message
    self.next_message = None

    while next_message:
      logging.info("Querying AI...")
      await self.conversation.SetState(ConversationState.WAITING_FOR_AI_RESPONSE
                                      )
      next_message = await self._process_ai_response(
          await self.ai_conversation.SendMessage(next_message))
    await self.conversation.SetState(ConversationState.DONE)

    for message in reversed(self.conversation.GetMessagesList()):
      for section in reversed(message.GetContentSections()):
        if section.command_output and section.command_output.task_done:
          return section.command_output.output_variables
    return VariableMap({})

  async def _get_human_guidance(self, prompt: str, summary: str,
                                content_prefix: str,
                                next_message: Message) -> bool:
    await self.conversation.SetState(ConversationState.WAITING_FOR_CONFIRMATION)
    guidance = await self.options.confirmation_state.RequireConfirmation(
        self.conversation.GetId(), prompt)
    if not guidance:
      logging.info("No guidance.")
      return False

    logging.info("Your guidance will be sent to the AI.")
    next_message.PushSection(
        ContentSection(
            content=f"{content_prefix}: {guidance}", summary=summary))
    return True

  async def _execute_one_command(
      self, cmd_input: CommandInput) -> list[ContentSection]:
    command_name = cmd_input.command_name
    command = self.options.commands_registry.Get(command_name)
    assert command
    command_output: CommandOutput = (await command.run(
        cmd_input.args))._replace(thought_signature=cmd_input.thought_signature)

    outputs: list[ContentSection] = []
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
  async def _execute_commands(
      self, commands: list[CommandInput]
  ) -> Tuple[list[ContentSection], CommandOutput | None]:
    outputs: list[ContentSection] = []
    for cmd_input in commands:
      outputs.extend(await self._execute_one_command(cmd_input))

    return outputs, next((o.command_output
                          for o in outputs
                          if o.command_output and o.command_output.task_done),
                         None)


class AgentLoopFactory(BaseAgentLoopFactory):

  def new(self, options: AgentLoopOptions) -> BaseAgentLoop:
    return AgentLoop(options)
