import glob
import logging
import os
import subprocess
import threading
from typing import Callable, List, Optional

from agent_command import CommandOutput
from agent_loop_options import AgentLoopOptions
from command_registry_factory import CreateCommandRegistry
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
    if result.stdout.strip():
      return result.stdout.splitlines()
    else:
      return ["No uncommitted changes (git diff is empty)."]
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


def _run_single_review(
    review_prompt_path: str,
    parent_options: AgentLoopOptions,
    agent_loop_runner: Callable[[AgentLoopOptions], None],
    review_suggestions: List[ContentSection],
    lock: threading.Lock,
    git_diff_output: List[str],
    original_task_prompt_content: Optional[List[str]],
):
  logging.info(f"Starting review for {review_prompt_path}...")

  review_prompt_content = ReadReviewPromptFile(review_prompt_path)
  review_file_name = os.path.basename(review_prompt_path)

  review_conversation_path = parent_options.conversation_path.replace(
      '.json', f'.{review_file_name}.review.json')
  review_conversation = parent_options.conversation_factory.New(
      name=f"AI Review ({review_file_name}): {parent_options.conversation.GetName()}"
  )

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

  review_registry = CreateCommandRegistry(
      file_access_policy=parent_options.file_access_policy,
      validation_manager=parent_options.validation_manager,
      start_new_task=_dummy_start_new_task,
      git_dirty_accept=True,
      can_write=False,
      can_start_tasks=False)
  review_registry.Register(SuggestCommand(add_suggestion_callback))

  review_start_sections: List[ContentSection] = [
      ContentSection(
          content=[
              "You are an AI review assistant. Your task is to review a code changes and provide suggestions for improvement.",
              "Use the #suggest command for each individual suggestion. Each should be a single, actionable suggestion.",
              "When you are done, issue #done.",
              "Example:",
              "#suggest <<",
              "File xyz.js could be extended to ...",
              "To do this, ...",
              "#end",
              "",
              "Original task prompt for the main agent:",
              *(original_task_prompt_content or
                ["No original task prompt content available."]),
              "",
              "Current Git Diff (showing uncommitted changes):",
              *git_diff_output,
              "",
              f"Review Guidelines (from {review_file_name}):",
              *review_prompt_content,
              "",
              "Available commands for review:",
          ],
          summary="Review context and guidelines for the AI"),
      ContentSection(
          content=review_registry.HelpText(),
          summary="Available commands for AI review")
  ]
  review_start_message = Message(
      'system', content_sections=review_start_sections)

  review_confirmation_state = ConfirmationState(
      confirmation_manager=parent_options.confirmation_state
      .confirmation_manager,
      confirm_every=None)

  review_options = AgentLoopOptions(
      conversation_factory=parent_options.conversation_factory,
      conversation_path=review_conversation_path,
      model=parent_options.model,
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
      original_task_prompt_content=None,
  )

  agent_loop_runner(review_options)
  logging.info(f"Nested review agent loop for {review_prompt_path} done.")


def run_parallel_reviews(
    parent_options: AgentLoopOptions,
    agent_loop_runner: Callable[[AgentLoopOptions], None],
    original_task_prompt_content: Optional[List[str]]
) -> Optional[List[ContentSection]]:
  """Runs reviews in parallel based on files in agent/review/*.txt.

  Args:
    parent_options: The options of the parent AgentLoop.
    agent_loop_runner: A callable that creates and runs a new AgentLoop.
    original_task_prompt_content: The content of the original task prompt.

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

  git_diff_output = GetGitDiffContent()

  review_suggestions: List[ContentSection] = []
  lock = threading.Lock()
  threads = []

  for review_file in review_files:
    thread = threading.Thread(
        target=_run_single_review,
        args=(
            review_file,
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
