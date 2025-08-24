import logging
import re
import sys
from typing import Dict, List, Optional, Pattern

from agent_loop import AgentLoop
from agent_loop_options import AgentLoopOptions
from confirmation import ConfirmationState
from conversation import Conversation, ConversationId, ConversationFactory
from message import Message, ContentSection
from conversation_state import ConversationState
import review_utils

from agent_workflow import AgentWorkflow, AgentWorkflowFactory
from agent_workflow_options import AgentWorkflowOptions


class ImplementAndReviewWorkflow(AgentWorkflow):

  def __init__(self, options: AgentWorkflowOptions) -> None:
    super().__init__(options)

    if not options.original_task_prompt_content:
      raise ValueError(
          "ImplementAndReviewWorkflow requires original_task_prompt_content in AgentWorkflowOptions."
      )
    self._original_task_prompt_content: str = options.original_task_prompt_content

    self._agent_loop = AgentLoop(options.agent_loop_options)
    self._confirm_done_regex: Optional[Pattern[str]] = re.compile(
        options.confirm_done) if options.confirm_done else None

  async def _RunReviews(self,
                        git_diff_output: str) -> Optional[List[ContentSection]]:
    await self._options.agent_loop_options.conversation.SetState(
        ConversationState.WAITING_FOR_REVIEW_FEEDBACK)

    return review_utils.reject_output_content_sections(
        await review_utils.run_parallel_reviews(
            reviews_to_run=review_utils.implementation_review_spec(
                parent_options=self._options.agent_loop_options,
                original_task_prompt_content=self._original_task_prompt_content,
                git_diff_output=git_diff_output),
            parent_options=self._options.agent_loop_options,
            conversation_factory=self._options.conversation_factory,
            expose_read_commands=True))

  async def _handle_initial_review(self) -> None:
    if self._options.review_first:
      logging.info("Running --review-first...")
      logging.info("Calling get_git_diff_content from _handle_initial_review")
      git_diff_output = review_utils.get_git_diff_content()
      if not git_diff_output:
        logging.error(
            "Cannot run --review-first with no uncommitted changes. Aborting.")
        sys.exit(1)

      review_feedback_content = await self._RunReviews(git_diff_output)
      if review_feedback_content:
        logging.info(
            f"Found {len(review_feedback_content)} review suggestions.")
        initial_message = self._options.agent_loop_options.start_message
        if not initial_message:
          initial_message = Message(role='system', content_sections=[])
        self._agent_loop.set_next_message(
            Message(
                role='system',
                content_sections=(review_feedback_content +
                                  initial_message.GetContentSections())))
      else:
        logging.info("No review suggestions found. Exiting.")
        sys.exit(0)

  async def _get_review_message(self) -> Optional[Message]:
    if not self._options.do_review:
      return None

    logging.info("Calling get_git_diff_content from _get_review_message")
    git_diff_output = review_utils.get_git_diff_content()
    if not git_diff_output:
      logging.info("No uncommitted changes; skipping review.")
      return None

    review_feedback_content = await self._RunReviews(git_diff_output)
    if not review_feedback_content:
      logging.info("No review feedback.")
      return None

    return Message(role='user', content_sections=review_feedback_content)

  async def _get_confirm_guidance(self) -> Optional[Message]:
    if not self._confirm_done_regex:
      return None

    await self._options.agent_loop_options.conversation.SetState(
        ConversationState.WAITING_FOR_CONFIRMATION)
    guidance = await self._options.agent_loop_options.confirmation_state.RequireConfirmation(
        self._options.agent_loop_options.conversation.GetId(),
        ("Confirm `done` command? "
         "Enter an empty string to accept and terminate, "
         "or some message to be sent to the AI asking it to continue."))
    if not guidance:
      return None

    logging.info("Your guidance will be sent to the AI.")
    return Message(
        role='user',
        content_sections=[
            ContentSection(
                content=f"Notice from human: {guidance}",
                summary="Human decision to continue")
        ])

  async def run(self) -> None:
    await self._handle_initial_review()

    while self._agent_loop.next_message:
      await self._agent_loop.run()
      next_message = await self._get_review_message(
      ) or await self._get_confirm_guidance()
      if next_message:
        self._agent_loop.set_next_message(next_message)


class ImplementAndReviewWorkflowFactory(AgentWorkflowFactory):

  def name(self) -> str:
    return "implement_and_review"

  async def new(self, options: AgentWorkflowOptions,
                args: Dict[str, str]) -> AgentWorkflow:
    task = args.get('original_task_prompt_content')
    # TODO: Get rid of this assert!
    assert task
    conversation = await options.conversation_factory.New(
        name='Submitted conversation',
        path=None,
        command_registry=options.agent_loop_options.commands_registry)
    content_sections = list(
        options.agent_loop_options.start_message.GetContentSections())
    content_sections.append(
        ContentSection(content=task, summary='Input from web form.'))
    start_message = Message('system', content_sections)
    return ImplementAndReviewWorkflow(
        options._replace(
            agent_loop_options=options.agent_loop_options._replace(
                conversation=conversation, start_message=start_message),
            original_task_prompt_content=task))
