import json
import openai
import logging
from conversation import Conversation, ConversationFactory, Message, MultilineContent, ContentSection
from typing import cast, Generator, List, Optional, Tuple, Union, Pattern, NamedTuple
from validation import ValidationManager

from confirmation import ConfirmationState
from command_registry import CommandRegistry, CreateCommandRegistry
from file_access_policy import FileAccessPolicy
from parsing import ExtractCommands
from validate_command_input import ValidateCommandInput
from conversational_ai import ConversationalAI
from review_utils import GetGitDiffContent, ReadReviewPromptFile
from review_commands import SuggestCommand
from selection_manager import SelectionManager
from task_command import TaskInformation
from agent_command import CommandOutput

logging.basicConfig(level=logging.INFO)

CONVERSATION_KEY = 'conversation'


class AgentLoopOptions(NamedTuple):
  conversation_factory: ConversationFactory
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
  do_review: bool = False
  original_task_prompt_content: Optional[List[str]] = None


# Dummy function for start_new_task when tasks are disabled for the registry
def _dummy_start_new_task(task_info: TaskInformation) -> CommandOutput:
  # This function should never be called because can_start_tasks is False
  # for the review registry. If it were called, it indicates a logic error.
  logging.error(
      f"Attempted to start a task within a review loop, but tasks are disabled. Task: {task_info.task_name}"
  )
  return CommandOutput(
      output=[],
      errors=["Task command is disabled in review mode."],
      summary="Task disabled in review mode.")


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
      logging.info("Querying ChatGPT...")
      response_message: Message = self.ai_conversation.SendMessage(next_message)
      self.conversation.Save(self.options.conversation_path)

      # TODO: Change ExtractCommands to receive a MultilineContent directly.
      commands, non_command_lines = ExtractCommands('\n'.join([
          '\n'.join(s.content) for s in response_message.GetContentSections()
      ]))

      next_message = Message(role='user')
      response_content_str = '\n'.join(
          ['\n'.join(s.content) for s in response_message.GetContentSections()])

      has_human_guidance = False
      if (self.options.confirm_regex and any(
          self.options.confirm_regex.match(ci.command_name)
          for ci in commands)) or non_command_lines:
        guidance = self.options.confirmation_state.RequireConfirmation(
            self.conversation.GetId(), response_content_str)
        if guidance:
          print("Your guidance will be sent to the AI.")
          next_message.PushSection(
              ContentSection(
                  content=[f"Message from human: {guidance}"],
                  summary="Human guidance for AI"))
          has_human_guidance = True

      self.options.confirmation_state.RegisterInteraction(
          self.conversation.GetId())

      command_outputs, should_terminate_agent_loop = self._ExecuteCommands(
          commands)
      for content_section in command_outputs:
        next_message.PushSection(content_section)

      if should_terminate_agent_loop and not has_human_guidance:
        logging.info("AgentLoop terminating as per command execution.")
        break

      if not self.options.skip_implicit_validation:
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

  def _ExecuteCommands(self, commands) -> Tuple[List[ContentSection], bool]:
    if not commands:
      return ([
          ContentSection(
              content=[
                  "Error: No commands found in response! Use #done if you are done with your task."
              ],
              summary="Error: No commands received")
      ], False)

    outputs: List[ContentSection] = []
    should_terminate_agent_loop: bool = False
    for cmd_input in commands:
      command_name = cmd_input.command_name
      if command_name == "done":
        should_terminate_agent_loop = True
        if self.options.do_review:
          review_feedback_content = self._RunReview()
          if review_feedback_content:
            should_terminate_agent_loop = False
            outputs.extend(review_feedback_content)

        if should_terminate_agent_loop and self.options.confirm_done:
          guidance = self.options.confirmation_state.RequireConfirmation(
              self.conversation.GetId(), "Confirm #done command? " +
              "Enter an empty string to accept and terminate, " +
              "or some message to be sent to the AI asking it to continue.")
          if guidance:
            logging.info("Your guidance will be sent to the AI.")
            outputs.append(
                ContentSection(
                    content=[f"Notice from human: {guidance}"],
                    summary="Human decision to continue"))
            should_terminate_agent_loop = False
        break

      command = self.options.commands_registry.Get(command_name)
      if not command:
        output = f"Error: Unknown command: {command_name}"
        logging.error(output)
        outputs.append(ContentSection(content=[output], summary=output))
        continue

      warnings = ValidateCommandInput(command.Syntax(), cmd_input,
                                      self.options.file_access_policy)
      if warnings:
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

    return outputs, should_terminate_agent_loop

  def _RunReview(self) -> Optional[List[ContentSection]]:
    logging.info("Initiating AI review...")

    git_diff_output = GetGitDiffContent()
    review_prompt_content = ReadReviewPromptFile()

    review_conversation_path = self.options.conversation_path.replace(
        '.json', '.review.json')
    review_conversation = self.options.conversation_factory.New(
        name="AI Review: " + self.conversation.GetName())

    review_suggestions: List[ContentSection] = []

    def add_suggestion_callback(text: MultilineContent) -> None:
      review_suggestions.append(
          ContentSection(
              content=[f"Suggestion {len(review_suggestions) + 1}: <<"] + text +
              ["#end"],
              summary=f"Review Suggestion {len(review_suggestions) + 1}"))

    review_selection_manager = SelectionManager()
    review_registry = CreateCommandRegistry(
        file_access_policy=self.options.file_access_policy,
        validation_manager=self.options.validation_manager,
        start_new_task=_dummy_start_new_task,
        git_dirty_accept=True,
        can_write=False,
        can_start_tasks=False)
    review_registry.Register(SuggestCommand(add_suggestion_callback))

    review_start_sections: List[ContentSection] = [
        ContentSection(
            content=[
                "You are an AI review assistant. Your task is to review a code changes and provide suggestions for improvement.",
                "Use the #suggest command for each individual suggestion you want to issue. Each #suggest command should contain a single, actionable suggestion.",
                "When you have no more suggestions, issue the #done command.",
                "",
                "Original task prompt for the main agent:",
                *(self.options.original_task_prompt_content or
                  ["No original task prompt content available."]),
                "",
                "Current Git Diff (showing uncommitted changes):",
                *git_diff_output,
                "",
                "Review Guidelines (from agent/review.txt):",
                *review_prompt_content,
                "",
                "Available commands for review:",
            ],
            summary="Review context and guidelines for the AI"),
        ContentSection(
            content=[review_registry.HelpText()],
            summary="Available commands for AI review")
    ]
    review_start_message = Message(
        'system', content_sections=review_start_sections)

    review_confirmation_state = ConfirmationState(
        confirmation_manager=self.options.confirmation_state
        .confirmation_manager,
        confirm_every=None)

    AgentLoop(
        AgentLoopOptions(
            conversation_factory=self.options.conversation_factory,
            conversation_path=review_conversation_path,
            model=self.options.model,
            conversation=review_conversation,
            start_message=review_start_message,
            commands_registry=review_registry,
            confirmation_state=review_confirmation_state,
            file_access_policy=self.options.file_access_policy,
            conversational_ai=self.options.conversational_ai,
            confirm_regex=None,
            confirm_done=False,
            skip_implicit_validation=True,
            validation_manager=None,
            do_review=False,
            original_task_prompt_content=None,
        )).run()

    if review_suggestions:
      logging.info(f"AI review found {len(review_suggestions)} suggestions.")
      review_suggestions.append(
          ContentSection(
              content=["Please try to address these suggestions."],
              summary="Instructions after review suggestions"))
      return review_suggestions
    else:
      logging.info("AI review found no suggestions.")
      return None
