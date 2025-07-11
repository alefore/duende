import glob
import logging
import os
import subprocess
import threading
from typing import Callable, List, Optional, NamedTuple, Dict, Any

from agent_command import CommandOutput
from agent_loop_options import AgentLoopOptions
from command_registry_factory import CreateReviewCommandRegistry
from confirmation import ConfirmationState
from conversation import Conversation
from message import ContentSection, Message
from file_access_policy import FileAccessPolicy
from review_commands import AcceptChange, RejectChange
from task_command import TaskInformation


def GetGitDiffContent() -> str:
  """Retrieves the git diff output for uncommitted changes."""
  try:
    result = subprocess.run(["git", "diff", "--unified=0"],
                            capture_output=True,
                            text=True,
                            check=True)
    return result.stdout
  except subprocess.CalledProcessError as e:
    logging.error(f"Failed to get git diff: {e}\nStderr: {e.stderr}")
    return f"Error getting git diff: {e.stderr}"
  except FileNotFoundError:
    logging.error("Git command not found. Cannot get git diff.")
    return "Warning: Git command not found. Cannot get git diff."
  except Exception as e:
    logging.error(f"An unexpected error occurred while getting git diff: {e}")
    return f"Error getting git diff: {e}"


def ReadReviewPromptFile(file_path: str) -> str:
  """Reads the content of the review prompt file."""
  with open(file_path, 'r') as f:
    return f.read()


class ReviewResult(NamedTuple):
  id: str
  command_output: CommandOutput
  is_accepted: bool


def _run_single_review(
    review_id: str,
    review_prompt_content: str,
    original_conversation_path: str,
    parent_options: AgentLoopOptions,
    agent_loop_runner: Callable[[AgentLoopOptions], None],
) -> ReviewResult:
  logging.info(f"Starting review for ID: {review_id}...")

  review_conversation_path = original_conversation_path.replace(
      '.json', f'.{review_id}.review.json')

  review_conversation = parent_options.conversation_factory.New(
      name=f"AI Review ({review_id}): {parent_options.conversation.GetName()}",
      path=review_conversation_path)

  # A list is used here to capture the result from the callbacks, as
  # Python closures for outer scope variables require mutable objects to
  # be modified within nested functions.
  single_review_result: List[ReviewResult] = []

  def add_review_result_callback(command_output: CommandOutput,
                                 is_accepted: bool) -> None:
    single_review_result.append(
        ReviewResult(
            id=review_id,
            command_output=command_output,
            is_accepted=is_accepted))

  review_registry = CreateReviewCommandRegistry(
      file_access_policy=parent_options.file_access_policy)
  review_registry.Register(
      AcceptChange(lambda command_output: add_review_result_callback(
          command_output, True)))
  review_registry.Register(
      RejectChange(lambda command_output: add_review_result_callback(
          command_output, False)))

  review_start_sections: List[ContentSection] = [
      ContentSection(
          content=review_prompt_content, summary="Generic review guidelines"),
  ]
  review_start_message = Message(
      'system', content_sections=review_start_sections)

  review_confirmation_state = ConfirmationState(
      confirmation_manager=parent_options.confirmation_state
      .confirmation_manager,
      confirm_every=None)

  review_options = AgentLoopOptions(
      task_prompt_content=parent_options.task_prompt_content,
      conversation_factory=parent_options.conversation_factory,
      conversation=review_conversation,
      start_message=review_start_message,
      commands_registry=review_registry,
      confirmation_state=review_confirmation_state,
      file_access_policy=parent_options.file_access_policy,
      conversational_ai=parent_options.conversational_ai,
      confirm_regex=None,
      skip_implicit_validation=True,
      validation_manager=None,
  )

  logging.info(f"Starting review for {review_id}.")
  agent_loop_runner(review_options)
  logging.info(f"Nested review agent loop for {review_id} done.")

  assert single_review_result, "Review agent did not call accept/reject. This should never happen."
  return single_review_result[0]


def run_parallel_reviews(
    reviews_to_run: Dict[str, str], parent_options: AgentLoopOptions,
    agent_loop_runner: Callable[[AgentLoopOptions],
                                None]) -> List[ReviewResult]:
  """Runs reviews in parallel based on the provided specifications.

  Args:
    reviews_to_run: A dictionary mapping an arbitrary ID (str) to the full
      review prompt string.
    parent_options: The options of the parent AgentLoop.
    agent_loop_runner: A callable that creates and runs a new AgentLoop.

  Returns:
    A list of ReviewResult objects, containing the outputs of all reviews.
  """
  logging.info("Initiating AI reviews...")

  if not reviews_to_run:
    logging.info("No reviews specified. Skipping parallel review.")
    return []

  review_results: List[ReviewResult] = []
  lock = threading.Lock()
  threads = []

  def run_and_collect_single_review(review_id: str,
                                    review_input_data: Dict[str, Any]) -> None:
    result = _run_single_review(
        review_id=review_id,
        review_prompt_content=review_input_data['review_prompt_content'],
        original_conversation_path=review_input_data[
            'original_conversation_path'],
        parent_options=parent_options,
        agent_loop_runner=agent_loop_runner,
    )
    with lock:
      review_results.append(result)

  for review_id, review_prompt_content in reviews_to_run.items():
    thread = threading.Thread(
        target=run_and_collect_single_review,
        args=(review_id, {
            'review_prompt_content': review_prompt_content,
            'original_conversation_path': parent_options.conversation.path,
        }),
    )
    threads.append(thread)
    thread.start()

  for thread in threads:
    thread.join()

  logging.info("All review threads finished.")
  logging.info(f"AI review found {len(review_results)} results.")

  return review_results


def implementation_review_spec(parent_options: AgentLoopOptions,
                               original_conversation_path: str,
                               original_task_prompt_content: str,
                               git_diff_output: str) -> Dict[str, str]:
  """Computes the dictionary of review specifications for implementation reviews.

  Args:
    parent_options: The options of the parent AgentLoop.
    original_conversation_path: The path to the original conversation file.
    original_task_prompt_content: The content of the original task prompt.
    git_diff_output: The git diff content to be reviewed.

  Returns:
    A dictionary mapping an arbitrary ID (str) to the full review prompt string.
  """
  reviews_to_run: Dict[str, str] = {}
  review_files = glob.glob('agent/review/*/prompt.txt')

  if not review_files:
    logging.info(
        "No review files found in agent/review/*.txt. No implementation reviews will be run."
    )
    return reviews_to_run

  for review_file_path in review_files:
    reviews_to_run[os.path.basename(os.path.dirname(review_file_path))] = (
        "### REVIEW CRITERIA\n\n" + ReadReviewPromptFile(review_file_path) +
        "\n\n### EVALUATION\n\n" +
        "You MUST use either the `accept_change` or `reject_change` command. As soon as you use either, the conversation terminates. You should use ReadFile to read any files relevant to make a good assessment.\n\n"
        + "### CHANGE\n\n" + "The change to review:\n\n" + git_diff_output +
        "\n\n### GOAL OF THIS CHANGE\n\n" +
        f"Original goal of this change:\n\n" + original_task_prompt_content)

  return reviews_to_run


def reject_output_content_sections(
    all_review_results: List[ReviewResult]) -> Optional[List[ContentSection]]:
  """Processes the output of run_parallel_reviews, turning rejections into
  an optional list of content sections.

  Args:
    all_review_results: A list of ReviewResult objects from run_parallel_reviews.

  Returns:
    A list of content sections with rejection reasons, or None if all review
    evaluators accepted the change.
  """
  if not all_review_results:
    logging.info("No review results provided.")
    return None

  if all(result.is_accepted for result in all_review_results):
    logging.info("All reviews accepted the change.")
    return None

  logging.info("Some reviews rejected the change.")
  feedback_sections: List[ContentSection] = [
      ContentSection(
          content="Please consider addressing the following issues that caused the evaluatores to reject your change and try again.",
          summary="Instructions about review results")
  ]
  feedback_sections.extend([
      ContentSection(
          content=f"Evaluator {r.id} found issues with your change:\n\n{r.command_output.output}",
          summary=f"Review rejection from {r.id}")
      for r in all_review_results
      if not r.is_accepted
  ])
  return feedback_sections
