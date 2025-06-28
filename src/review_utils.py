import glob
import logging
import os
import subprocess
import threading
from typing import Callable, List, Optional

from agent_command import CommandOutput
from agent_loop_options import AgentLoopOptions
from command_registry_factory import CreateReviewCommandRegistry
from confirmation import ConfirmationState
from conversation import ContentSection, Message, MultilineContent
from file_access_policy import FileAccessPolicy
from review_commands import SuggestCommand
from task_command import TaskInformation


def _dummy_start_new_task(task_info: TaskInformation) -> CommandOutput:
  logging.error(
      f"Attempted to start a task within a review loop, but tasks are disabled. Task: {task_info.task_name}"
  )
  return CommandOutput(
      output=[],
      errors=["Task command is disabled in review mode."],
      summary="Task disabled in review mode.")


def GetGitDiffContent() -> List[str]:
  """Retrieves the git diff output for uncommitted changes."""
  try:
    result = subprocess.run(["git", "diff", "--unified=0"],
                            capture_output=True,
                            text=True,
                            check=True)
    return result.stdout.splitlines()
  except subprocess.CalledProcessError as e:
    logging.error(f"Failed to get git diff: {e}\nStderr: {e.stderr}")
    return [f"Error getting git diff: {e.stderr}"]
  except FileNotFoundError:
    logging.error("Git command not found. Cannot get git diff.")
    return ["Warning: Git command not found. Cannot get git diff."]
  except Exception as e:
    logging.error(f"An unexpected error occurred while getting git diff: {e}")
    return [f"Error getting git diff: {e}"]


def ReadReviewPromptFile(file_path: str) -> List[str]:
  """Reads the content of the review prompt file."""
  with open(file_path, 'r') as f:
    return [l.rstrip() for l in f.readlines()]


def _run_single_review(review_prompt_path: str, original_conversation_path: str,
                       parent_options: AgentLoopOptions,
                       agent_loop_runner: Callable[[AgentLoopOptions], None],
                       review_suggestions: List[ContentSection],
                       lock: threading.Lock, git_diff_output: List[str],
                       original_task_prompt_content: List[str]) -> None:
  logging.info(f"Starting review for {review_prompt_path}...")

  review_prompt_content = ReadReviewPromptFile(review_prompt_path)
  review_file_name = os.path.basename(review_prompt_path).replace('.txt', '')

  review_conversation_path = original_conversation_path.replace(
      '.json', f'.{review_file_name}.review.json')

  review_conversation = parent_options.conversation_factory.New(
      name=f"AI Review ({review_file_name}): {parent_options.conversation.GetName()}",
      path=review_conversation_path)

  def add_suggestion_callback(text: MultilineContent) -> None:
    with lock:
      index = len(review_suggestions) + 1
      logging.info(
          f"Adding suggestion from {review_file_name}: suggestion #{index}")
      review_suggestions.append(
          ContentSection(
              content=[
                  f"Suggestion {index} (from {review_file_name}): <<",
              ] + text + ["#end"],
              summary=f"Review Suggestion {index} from {review_file_name}"))

  review_registry = CreateReviewCommandRegistry(
      file_access_policy=parent_options.file_access_policy)
  review_registry.Register(SuggestCommand(add_suggestion_callback))

  review_start_sections: List[ContentSection] = [
      ContentSection(
          content=[
              "### TASK",
              "",
              *original_task_prompt_content,
              "",
              "### ISSUING SUGGESTIONS",
              "",
              "If the code looks good, just respond with `#done`.",
              "",
              "Otherwise, emit suggestions which should be specific, be actionable, and include an explanation of how they are directly related with the aforementioned task.",
              "",
              "Use `#suggest` for each individual suggestion (followed by multi-line content and the line `#end`) and `#done` after all suggestions. Example:",
              "",
              "#suggest <<",
              "File xyz.js could be extended to ...",
              "",
              "To do this, consider ...",
              "",
              "This is related with the task because ...",
              "#end",
              "#suggest <<",
              "This code could be modified to avoid ...",
              "",
              "The best way to achieve this would be ...",
              "",
              "This is related with the task because ...",
              "#end",
              "#done",
              "",
              "### CHANGE",
              "",
              "The change to review:",
              "",
              *git_diff_output,
              "",
              "### GOAL OF THIS CHANGE",
              "",
              f"Original goal of this change:",
              "",
              *review_prompt_content,
          ],
          summary="Generic review guidelines"),
  ]
  review_start_message = Message(
      'system', content_sections=review_start_sections)

  review_confirmation_state = ConfirmationState(
      confirmation_manager=parent_options.confirmation_state
      .confirmation_manager,
      confirm_every=None)

  review_options = AgentLoopOptions(
      task_prompt_content=original_task_prompt_content,
      conversation_factory=parent_options.conversation_factory,
      conversation=review_conversation,
      start_message=review_start_message,
      commands_registry=review_registry,
      confirmation_state=review_confirmation_state,
      file_access_policy=parent_options.file_access_policy,
      conversational_ai=parent_options.conversational_ai,
      confirm_regex=None,
      confirm_done=False,
      skip_implicit_validation=True,
      validation_manager=None,
      do_review=False,
      review_first=False,
  )

  agent_loop_runner(review_options)
  logging.info(f"Nested review agent loop for {review_prompt_path} done.")


def run_parallel_reviews(
    parent_options: AgentLoopOptions, original_conversation_path: str,
    agent_loop_runner: Callable[[AgentLoopOptions],
                                None], original_task_prompt_content: List[str],
    git_diff_output: List[str]) -> Optional[List[ContentSection]]:
  """Runs reviews in parallel based on files in agent/review/*.txt.

  Args:
    parent_options: The options of the parent AgentLoop.
    agent_loop_runner: A callable that creates and runs a new AgentLoop.
    original_task_prompt_content: The content of the original task prompt.
    git_diff_output: The git diff content to be reviewed.

  Returns:
    A list of content sections with review suggestions, or None if no
    suggestions were made.
  """
  logging.info("Initiating AI reviews...")

  review_files = glob.glob('agent/review/*.txt')
  if not review_files:
    logging.info(
        "No review files found in agent/review/*.txt. Skipping review.")
    return None

  review_suggestions: List[ContentSection] = []
  lock = threading.Lock()
  threads = []

  for review_file in review_files:
    thread = threading.Thread(
        target=_run_single_review,
        args=(
            review_file,
            original_conversation_path,
            parent_options,
            agent_loop_runner,
            review_suggestions,
            lock,
            git_diff_output,
            original_task_prompt_content,
        ))
    threads.append(thread)
    thread.start()

  for thread in threads:
    thread.join()

  logging.info("All review threads finished.")

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
