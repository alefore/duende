import logging
import re
import sys
from typing import List, Optional, Pattern

from agent_loop import AgentLoop
from agent_loop_options import AgentLoopOptions
from confirmation import ConfirmationState
from conversation import Conversation, ConversationId, ConversationFactory
from message import Message, ContentSection
from conversation_state import ConversationState
import review_utils

from agent_workflow import AgentWorkflow


class ImplementAndReviewWorkflow(AgentWorkflow):

  def __init__(self,
               options: AgentLoopOptions,
               confirm_done: str = '',
               do_review: bool = False,
               review_first: bool = False) -> None:
    super().__init__(options.conversation_factory)
    self._options = options
    self._agent_loop = AgentLoop(options)
    self._confirm_done_regex: Optional[Pattern[str]] = re.compile(
        confirm_done) if confirm_done else None
    self._do_review = do_review
    self._review_first = review_first

  def _RunReviews(self, git_diff_output: str) -> Optional[List[ContentSection]]:
    self._options.conversation.SetState(
        ConversationState.WAITING_FOR_REVIEW_FEEDBACK)

    def agent_loop_runner(options: AgentLoopOptions) -> None:
      AgentLoop(options).run()

    return review_utils.run_parallel_reviews(
        parent_options=self._options,
        original_conversation_path=self._agent_loop.conversation.path,
        agent_loop_runner=agent_loop_runner,
        original_task_prompt_content=self._options.task_prompt_content,
        git_diff_output=git_diff_output)

  def _handle_initial_review(self) -> None:
    if self._review_first:
      logging.info("Running --review-first...")
      logging.info("Calling GetGitDiffContent from _handle_initial_review")
      git_diff_output = review_utils.GetGitDiffContent()
      if not git_diff_output:
        logging.error(
            "Cannot run --review-first with no uncommitted changes. Aborting.")
        sys.exit(1)

      review_feedback_content = self._RunReviews(git_diff_output)
      if review_feedback_content:
        logging.info(
            f"Found {len(review_feedback_content)} review suggestions.")
        initial_message = self._options.start_message
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

  def _get_review_message(self) -> Optional[Message]:
    if not self._do_review:
      return None

    logging.info("Calling GetGitDiffContent from _get_review_message")
    git_diff_output = review_utils.GetGitDiffContent()
    if not git_diff_output:
      logging.info("No uncommitted changes; skipping review.")
      return None

    review_feedback_content = self._RunReviews(git_diff_output)
    if not review_feedback_content:
      logging.info("No review feedback.")
      return None

    return Message(role='user', content_sections=review_feedback_content)

  def _get_confirm_guidance(self) -> Optional[Message]:
    if not self._confirm_done_regex:
      return None

    self._options.conversation.SetState(
        ConversationState.WAITING_FOR_CONFIRMATION)
    guidance = self._options.confirmation_state.RequireConfirmation(
        self._options.conversation.GetId(), ("Confirm `done` command? "
              "Enter an empty string to accept and terminate, "
              "or some message to be sent to the AI asking it to continue."))
    if not guidance:
      return None

    logging.info("Your guidance will be sent to the AI.")
    return Message(role='user', content_sections=[
        ContentSection(
            content=f"Notice from human: {guidance}",
            summary="Human decision to continue")
    ])

  def run(self) -> None:
    self._handle_initial_review()

    while self._agent_loop.next_message:
      self._agent_loop.run()
      next_message = self._get_review_message() or self._get_confirm_guidance()
      if next_message:
        self._agent_loop.set_next_message(next_message)
