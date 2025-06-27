import json
import openai
import logging
from conversation import Conversation, ConversationFactory, Message, ContentSection
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
from parsing import ExtractCommands
import review_utils
from validate_command_input import ValidateCommandInput

logging.basicConfig(level=logging.INFO)


class AgentLoop:

  def __init__(self, options: AgentLoopOptions):
    self.options = options
    self.conversation = self.options.conversation
    self.ai_conversation = options.conversational_ai.StartConversation(
        self.conversation)

  def run(self) -> None:
    logging.info("Starting AgentLoop run method...")
    next_message: Message = self.options.start_message
    while True:
      logging.info("Querying AI...")
      self.conversation.SetState(ConversationState.WAITING_FOR_AI_RESPONSE)
      response_message: Message = self.ai_conversation.SendMessage(next_message)
      self.conversation.Save(self.options.conversation_path)

      response_lines: List[str] = []
      for s in response_message.GetContentSections():
        response_lines.extend(s.content)

      self.conversation.SetState(ConversationState.PARSING_COMMANDS)
      commands, non_command_lines = ExtractCommands(response_lines)

      next_message = Message(role='user')
      response_content_str = '\n'.join(response_lines)

      has_human_guidance = False
      if (self.options.confirm_regex and any(
          self.options.confirm_regex.match(ci.command_name)
          for ci in commands)) or non_command_lines:
        self.conversation.SetState(ConversationState.WAITING_FOR_CONFIRMATION)
        guidance = self.options.confirmation_state.RequireConfirmation(
            self.conversation.GetId(), "Accept input?")
        if guidance:
          print("Your guidance will be sent to the AI.")
          next_message.PushSection(
              ContentSection(
                  content=[f"Message from human: {guidance}"],
                  summary="Human guidance for AI"))
          has_human_guidance = True

      self.options.confirmation_state.RegisterInteraction(
          self.conversation.GetId())

      self.conversation.SetState(ConversationState.RUNNING_COMMANDS)
      command_outputs, done_command_received = self._ExecuteCommands(commands)
      for content_section in command_outputs:
        next_message.PushSection(content_section)

      if done_command_received and self._HandleDoneCommand(next_message):
        break

      if not self.options.skip_implicit_validation:
        self.conversation.SetState(
            ConversationState.EXECUTING_IMPLICIT_VALIDATION)
        assert self.options.validation_manager
        validation_result = self.options.validation_manager.Validate()
        if not validation_result.success:
          logging.info(
              f"Validation failed: {'\\n'.join(validation_result.error)}")
          next_message.PushSection(
              ContentSection(
                  content=[
                      "The validation command is currently reporting failures "
                      "(normal if you are in the middle of applying changes). "
                      "To see the failures, use: #validate"
                  ],
                  summary="Validation status (failures detected)"))

  # Return value indicates whether #done was received.
  def _ExecuteCommands(
      self, commands: List[CommandInput]) -> Tuple[List[ContentSection], bool]:
    if not commands:
      return ([
          ContentSection(
              content=[
                  "Error: No commands found in response! Use #done if you are done with your task."
              ],
              summary="Error: No commands received")
      ], False)

    outputs: List[ContentSection] = []
    for cmd_input in commands:
      command_name = cmd_input.command_name
      if command_name == "done":
        return outputs, True

      command = self.options.commands_registry.Get(command_name)
      if not command:
        output = f"Error: Unknown command: {command_name}"
        logging.error(output)
        outputs.append(ContentSection(content=[output], summary=output))
        continue

      warnings = ValidateCommandInput(command.Syntax(), cmd_input,
                                      self.options.file_access_policy)
      if warnings:
        logging.info(f"Warnings: {','.join(warnings)}")
        outputs.append(
            ContentSection(
                content=[
                    f"Warning {command_name}: {warning}" for warning in warnings
                ],
                summary=f"Command '{command_name}' validation warnings"))
        continue

      command_output = command.Execute(cmd_input)
      if command_output.output:
        outputs.append(
            ContentSection(
                content=command_output.output,
                summary=command_output.summary or
                f"Output for command '{command_name}'"))
      if command_output.errors:
        outputs.append(
            ContentSection(
                content=[f"Error: {e}" for e in command_output.errors],
                summary=f"Errors for command '{command_name}'"))
      logging.info(command_output.summary)

    return outputs, False

  def _HandleDoneCommand(self, next_message: Message) -> bool:
    if self.options.do_review:

      def agent_loop_runner(options: AgentLoopOptions) -> None:
        AgentLoop(options).run()

      self.conversation.SetState(ConversationState.WAITING_FOR_REVIEW_FEEDBACK)
      review_feedback_content: Optional[
          List[ContentSection]] = review_utils.run_parallel_reviews(
              parent_options=self.options,
              agent_loop_runner=agent_loop_runner,
              original_task_prompt_content=self.options.task_prompt_content)
      if review_feedback_content:
        for section in review_feedback_content:
          next_message.PushSection(section)
        return False

    if self.options.confirm_done:
      self.conversation.SetState(ConversationState.WAITING_FOR_CONFIRMATION)
      guidance = self.options.confirmation_state.RequireConfirmation(
          self.conversation.GetId(), "Confirm #done command? " +
          "Enter an empty string to accept and terminate, " +
          "or some message to be sent to the AI asking it to continue.")
      if guidance:
        logging.info("Your guidance will be sent to the AI.")
        next_message.PushSection(
            ContentSection(
                content=[f"Notice from human: {guidance}"],
                summary="Human decision to continue"))
        return False

    return True
