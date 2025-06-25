import json
import openai
import logging
from conversation import Conversation, Message, MultilineContent
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
from select_commands import SelectionManager
from task_command import TaskInformation, CommandOutput

logging.basicConfig(level=logging.INFO)

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
  do_review: bool = False
  original_task_prompt_content: Optional[List[str]] = None


# Dummy function for start_new_task when tasks are disabled for the registry
def _dummy_start_new_task(task_info: TaskInformation) -> CommandOutput:
    # This function should never be called because can_start_tasks is False
    # for the review registry. If it were called, it indicates a logic error.
    logging.error(f"Attempted to start a task within a review loop, but tasks are disabled. Task: {task_info.task_name}")
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
    # This line is reverted to its original, correct form.
    # next_message is the input message for the AI for the current turn.
    next_message: Message = self.options.start_message
    while True:
      logging.info("Querying ChatGPT...")
      response_message: Message = self.ai_conversation.SendMessage(next_message)
      self.conversation.Save(self.options.conversation_path)

      commands, non_command_lines = ExtractCommands('\n'.join(
          ['\n'.join(s) for s in response_message.GetContentSections()]))

      next_message = Message(role='user') # Re-initialize for the next turn's input
      response_content_str = '\n'.join(
          ['\n'.join(s) for s in response_message.GetContentSections()])
      if (self.options.confirm_regex and any(
          self.options.confirm_regex.match(ci.command_name)
          for ci in commands)) or non_command_lines:
        guidance = self.options.confirmation_state.RequireConfirmation(
            response_content_str)
        if guidance:
          print("Your guidance will be sent to the AI.")
          next_message.PushSection([f"Message from human: {guidance}"])

      self.options.confirmation_state.RegisterInteraction()
      for output_section in self._ExecuteCommands(commands):
        next_message.PushSection(output_section)

      if not self.options.skip_implicit_validation:
        assert self.options.validation_manager
        validation_result = self.options.validation_manager.Validate()
        if validation_result.returncode != 0:
          logging.info(f"Validation failed: {validation_result.returncode}")
          next_message.PushSection([
              "The validation command is currently reporting failures "
              "(normal if you are in the middle of applying changes). "
              "To see the failures, use: #validate"
          ])

  def _ExecuteCommands(self,
                       commands) -> Generator[MultilineContent, None, None]:
    if not commands:
      yield [
          "Error: No commands found in response! Use #done if you are done with your task."
      ]
      return

    for cmd_input in commands:
      if cmd_input.command_name == "done":
        if self.options.do_review:
          review_feedback_content = self._RunReview()
          if review_feedback_content:
            yield from review_feedback_content
            return

        if self.options.confirm_done:
          guidance = self.options.confirmation_state.RequireConfirmation(
              "Confirm #done command? Enter an empty string to accept and terminate, or some message to be sent to the AI asking it to continue."
          )
          if guidance:
            logging.info("Your guidance will be sent to the AI.")
            yield [f"Notice from human: {guidance}"]
            continue
        return

      command = self.options.commands_registry.Get(cmd_input.command_name)
      if not command:
        output = f"Unknown command: {cmd_input.command_name}"
        logging.error(output)
        yield [output]
        continue

      warnings = ValidateCommandInput(command.Syntax(), cmd_input,
                                      self.options.file_access_policy)
      if warnings:
        yield [
            f"Warning {cmd_input.command_name}: {warning}"
            for warning in warnings
        ]
        continue

      command_output = command.Execute(cmd_input)
      if command_output.output:
        yield command_output.output
      if command_output.errors:
        yield [f"Error: {e}" for e in command_output.errors]
      logging.info(command_output.summary)

  def _RunReview(self) -> Optional[List[MultilineContent]]:
    logging.info("Initiating AI review...")

    git_diff_output = GetGitDiffContent()
    review_prompt_content = ReadReviewPromptFile()

    review_conversation_path = self.options.conversation_path.replace(
        '.json', '.review.json')
    review_conversation = Conversation()

    review_suggestions: List[MultilineContent] = []

    def add_suggestion_callback(text: MultilineContent) -> None:
      review_suggestions.append(
          [f"Suggestion {len(review_suggestions) + 1}: <<"] + text + ["#end"])

    review_selection_manager = SelectionManager()
    review_registry = CreateCommandRegistry(
        file_access_policy=self.options.file_access_policy,
        validation_manager=self.options.validation_manager,
        start_new_task=_dummy_start_new_task,
        git_dirty_accept=True,
        can_write=False,
        can_start_tasks=False
    )
    review_registry.Register(SuggestCommand(add_suggestion_callback))


    review_start_sections: List[MultilineContent] = [[
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
    ], [review_registry.HelpText()]]
    review_start_message = Message(
        'system', content_sections=review_start_sections)

    review_confirmation_state = ConfirmationState(
        confirmation_manager=self.options.confirmation_state
        .confirmation_manager,
        confirm_every=None)

    AgentLoop(
        AgentLoopOptions(
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
      review_suggestions.append(["Please try to address these suggestions."])
      return review_suggestions
    else:
      logging.info("AI review found no suggestions.")
      return None
