import argparse
import logging
import re
import os
from typing import Optional, Pattern
from agent_loop import (LoadOpenAIAPIKey, CreateFileAccessPolicy,
                        TestFileAccess, CreateValidationManager,
                        CreateCommandRegistry, LoadOrCreateConversation,
                        AgentLoop, CommandRegistry, ValidationManager)
from file_access_policy import FileAccessPolicy


def parse_arguments() -> argparse.Namespace:
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--api_key', type=str, default=os.path.expanduser('~/.openai/api_key'))
  parser.add_argument(
      '--task',
      type=str,
      required=True,
      help="File path for task prompt. The conversation will be stored in a corresponding .conversation.json file."
  )
  parser.add_argument(
      '--model',
      type=str,
      default='gpt-4o',
      help="The model name to use for OpenAI API requests.")
  parser.add_argument(
      '--file_access_regex',
      type=str,
      help="Regex to match allowed file paths. Defaults to allowing all paths. Match is based on relative path to current directory."
  )
  parser.add_argument(
      '--confirm',
      type=str,
      default='',
      help="Regex to match commands requiring confirmation before execution.")
  parser.add_argument(
      '--test_file_access',
      action='store_true',
      help="Test the file access policy by listing all matched files and exit.")
  parser.add_argument(
      '--confirm_done',
      action='store_true',
      help="Require confirmation before executing the done command.")
  return parser.parse_args()


def main() -> None:
  args: argparse.Namespace = parse_arguments()

  LoadOpenAIAPIKey(args.api_key)

  file_access_policy: FileAccessPolicy = CreateFileAccessPolicy(
      args.file_access_regex)

  if args.test_file_access:
    TestFileAccess(file_access_policy)
    return

  validation_manager: Optional[ValidationManager] = CreateValidationManager()
  if validation_manager:
    initial_validation_result = validation_manager.Validate()
    if initial_validation_result and initial_validation_result.returncode != 0:
      logging.error("Initial validation failed, aborting further operations.")
      return

  registry: CommandRegistry = CreateCommandRegistry(file_access_policy,
                                                    validation_manager)
  messages, conversation_path = LoadOrCreateConversation(args.task, registry)

  confirm_regex: Optional[Pattern] = re.compile(
      args.confirm) if args.confirm else None
  loop: AgentLoop = AgentLoop(args.model, messages, registry, confirm_regex,
                              args.confirm_done)
  loop.run()


if __name__ == '__main__':
  main()
