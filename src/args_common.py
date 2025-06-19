import argparse
import os
import re
import sys
from typing import Optional, Pattern, List, Tuple
from agent_loop import AgentLoopOptions, Message, LoadConversation
from confirmation import ConfirmationState, ConfirmationManager, CLIConfirmationManager
from file_access_policy import FileAccessPolicy, RegexFileAccessPolicy, CurrentDirectoryFileAccessPolicy, CompositeFileAccessPolicy
from list_files import list_all_files
from command_registry import CommandRegistry, CreateCommandRegistry
from validation import CreateValidationManager
from task_command import CommandOutput, TaskInformation


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
  parser.add_argument(
      '--confirm_every',
      type=int,
      help="Require confirmation after every N interactions.")
  parser.add_argument(
      '--skip_implicit_validation',
      action='store_true',
      default=False,
      help="By default, we run the validation command each interaction. If this is given, only validates when explicitly request (by the AI)."
  )
  return parser


def CreateAgentLoopOptions(
    args: argparse.Namespace,
    confirmation_manager: ConfirmationManager) -> AgentLoopOptions:
  file_access_policy = CreateFileAccessPolicy(args.file_access_regex)

  # List files and check if any match the access policy
  if not list(list_all_files('.', file_access_policy)):
    print("No files match the given file access policy. Aborting execution.")
    sys.exit(1)  # Exit with a non-zero status to indicate failure

  if args.test_file_access:
    TestFileAccess(file_access_policy)
    sys.exit(0)  # Graceful exit after testing

  confirm_regex: Optional[Pattern] = re.compile(
      args.confirm) if args.confirm else None

  validation_manager = CreateValidationManager()

  if not args.skip_implicit_validation and not validation_manager:
    raise RuntimeError(
        "Validation script is not available; consider using --skip_implicit_validation."
    )

  if validation_manager:
    initial_validation_result = validation_manager.Validate()
    if initial_validation_result and initial_validation_result.returncode != 0:
      raise RuntimeError(
          "Initial validation failed, aborting further operations.")

  registry = CreateCommandRegistry(
      file_access_policy,
      validation_manager,
      start_new_task=lambda task_info: CommandOutput(
          output=[],
          errors=["TaskCommand execution not implemented"],
          summary="Not implemented"))

  conversation_path = re.sub(r'\.txt$', '.conversation.json', args.task)
  messages = LoadOrCreateConversation(args.task, conversation_path, registry)

  confirmation_state = ConfirmationState(
      confirmation_manager=confirmation_manager,
      confirm_every=args.confirm_every)

  return AgentLoopOptions(
      conversation_path=conversation_path,
      model=args.model,
      messages=messages,
      confirmation_state=confirmation_state,
      commands_registry=registry,
      confirm_regex=confirm_regex,
      skip_implicit_validation=args.skip_implicit_validation,
      validation_manager=validation_manager)


def LoadOrCreateConversation(prompt_path: str, conversation_path: str,
                             registry: CommandRegistry) -> List[Message]:

  messages = LoadConversation(conversation_path)
  if not messages:
    prompt = (
        "You are a coding assistant operating in a command loop environment. "
        "Use commands prefixed with `#`. "
        "Anything that is not a command will be relayed to the human.\n\n")

    agent_prompt_path = 'agent/prompt.txt'
    if os.path.exists(agent_prompt_path):
      with open(agent_prompt_path, 'r') as f:
        prompt += f.read() + "\n\n"

    with open(prompt_path, 'r') as f:
      prompt += f.read() + "\n\n"

    prompt += (
        "Some commands accept multi-line information, like this:\n\n"
        "#write_file foo.py <<\n"
        "line0\n"
        "line1\n"
        "…\n"
        "#end\n\n"
        "When you're done (or if you get stuck), "
        "issue #done to notify the human and stop this conversation.\n\n"
        "Anything sent outside of commands will be treated as plain text.\n\n"
        "You can send many commands per message. "
        "For example, if you want to read 5 files, "
        "you can issue 5 #read_file commands at once.\n\n")
    prompt += "Available commands:\n" + registry.HelpText()
    messages.append({'role': 'system', 'content': prompt})

  return messages


def CreateFileAccessPolicy(
    file_access_regex: Optional[str]) -> FileAccessPolicy:
  policies: List[FileAccessPolicy] = [CurrentDirectoryFileAccessPolicy()]
  if file_access_regex:
    policies.append(RegexFileAccessPolicy(file_access_regex))
  return CompositeFileAccessPolicy(policies)


def TestFileAccess(file_access_policy: FileAccessPolicy):
  for file in list_all_files('.', file_access_policy):
    print(file)
