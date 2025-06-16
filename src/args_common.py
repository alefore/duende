import argparse
import os
import re
import sys
from typing import Optional, Pattern
from agent_loop import AgentLoopOptions, LoadOrCreateConversation, CreateCommandRegistry, CreateFileAccessPolicy, CreateValidationManager, TestFileAccess
from confirmation import CLIConfirmationManager


def CreateCommonParser() -> argparse.ArgumentParser:
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
      '--test_file_access',
      action='store_true',
      help="Test the file access policy by listing all matched files and exit.")
  parser.add_argument(
      '--confirm',
      type=str,
      default='',
      help="Regex to match commands requiring confirmation before execution.")
  return parser


def CreateAgentLoopOptions(args: argparse.Namespace) -> AgentLoopOptions:
  file_access_policy = CreateFileAccessPolicy(args.file_access_regex)
  if args.test_file_access:
    TestFileAccess(file_access_policy)
    sys.exit(0)  # Graceful exit after testing

  confirm_regex: Optional[Pattern] = re.compile(
      args.confirm) if args.confirm else None

  validation_manager = CreateValidationManager()

  if validation_manager:
    initial_validation_result = validation_manager.Validate()
    if initial_validation_result and initial_validation_result.returncode != 0:
      raise RuntimeError(
          "Initial validation failed, aborting further operations.")

  registry = CreateCommandRegistry(file_access_policy, validation_manager)

  messages, _ = LoadOrCreateConversation(args.task, registry)

  return AgentLoopOptions(
      model=args.model,
      messages=messages,
      commands_registry=registry,
      confirm_regex=confirm_regex,
      confirmation_manager=CLIConfirmationManager())
