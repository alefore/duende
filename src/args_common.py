import argparse
import logging
import os
import re
import sys
from typing import Any, Callable, List, NamedTuple, Optional, Pattern, Tuple

from agent_loop_options import AgentLoopOptions
from confirmation import ConfirmationState, ConfirmationManager, CLIConfirmationManager
from file_access_policy import FileAccessPolicy, RegexFileAccessPolicy, CurrentDirectoryFileAccessPolicy, CompositeFileAccessPolicy
from list_files import list_all_files
from command_registry import CommandRegistry
from command_registry_factory import CreateCommandRegistry
from validation import CreateValidationManager, ValidationManager
from agent_command import CommandOutput
from chatgpt import ChatGPT
from conversation import Conversation, ConversationFactory, ConversationFactoryOptions
from message import Message, ContentSection
from conversational_ai import ConversationalAI
from gemini import Gemini
from validate_command_input import ValidateCommandInput


# Used to tell if a flag was set explicitly (which argparse doesn't directly
# support.
class TrackedFlagStr(NamedTuple):
  value: str
  set_explicitly: bool


class TrackFlagStrAction(argparse.Action):

  def __call__(self,
               parser: argparse.ArgumentParser,
               namespace: argparse.Namespace,
               values: Any,
               option_string: Optional[str] = None) -> None:
    setattr(namespace, self.dest, TrackedFlagStr(values, True))


def CreateCommonParser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--api-key',
      dest='api_key',
      type=str,
      default=os.path.expanduser('~/.openai/api_key'))
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
      '--file-access-regex',
      dest='file_access_regex',
      type=str,
      help="Regex to match allowed file paths. Defaults to allowing all paths. Match is based on relative path to current directory."
  )
  parser.add_argument(
      '--file-access-regex-path',
      dest='file_access_regex_path',
      type=str,
      default=TrackedFlagStr('agent/file-access-regex.txt', False),
      action=TrackFlagStrAction,
      help="File path to a regex to match allowed file paths. Ignored if --file-access-regex is given."
  )
  parser.add_argument(
      '--test-file-access',
      dest='test_file_access',
      action='store_true',
      help="Test the file access policy by listing all matched files and exit.")
  parser.add_argument(
      '--confirm',
      type=str,
      default='',
      help="Regex to match commands requiring confirmation before execution.")
  parser.add_argument(
      '--confirm-every',
      dest='confirm_every',
      type=int,
      help="Require confirmation after every N interactions.")
  parser.add_argument(
      '--skip-implicit-validation',
      dest='skip_implicit_validation',
      action='store_true',
      default=False,
      help="By default, we run the validation command each interaction. If this is given, only validates when explicitly request (by the AI)."
  )
  parser.add_argument(
      '--git-dirty-accept',
      dest='git_dirty_accept',
      action='store_true',
      default=False,
      help="Allow the program to proceed even if the Git repository has uncommitted changes."
  )
  parser.add_argument(
      '--review',
      action='store_true',
      help="Trigger an AI review of changes when the agent loop issues the #done command. The review happens in a new conversation."
  )
  parser.add_argument(
      '--review-first',
      action='store_true',
      help="Trigger an AI review of changes *before* the agent loop starts. If there are review comments, they are added to the initial prompt."
  )
  parser.add_argument(
      '--prompt-include',
      dest='prompt_include',
      action='append',
      default=[],
      help="Path to a file to include in the prompt. Can be specified multiple times."
  )
  return parser


def GetConversationalAI(args: argparse.Namespace,
                        command_registry: CommandRegistry) -> ConversationalAI:
  if args.model.startswith('gpt'):
    return ChatGPT(args.api_key, args.model)
  if args.model.startswith('gemini'):
    return Gemini(args.api_key, args.model, command_registry)
  raise Exception(f"Unknown AI: {args.model}")


def CreateAgentLoopOptions(
    args: argparse.Namespace, confirmation_manager: ConfirmationManager,
    conversation_factory_options: ConversationFactoryOptions
) -> AgentLoopOptions:
  file_access_policy = CreateFileAccessPolicy(args.file_access_regex,
                                              args.file_access_regex_path)

  matched_files = list(list_all_files('.', file_access_policy))
  logging.info(f"File matched by access policy: {len(matched_files)}")
  if not matched_files:
    print("No files match the given file access policy. Aborting execution.")
    sys.exit(1)

  if args.test_file_access:
    TestFileAccess(file_access_policy)
    sys.exit(0)

  confirm_regex: Optional[Pattern[str]] = re.compile(
      args.confirm) if args.confirm else None

  validation_manager = CreateValidationManager()

  if not args.skip_implicit_validation and not validation_manager:
    raise RuntimeError(
        "Validation script is not available; consider using --skip_implicit_validation."
    )

  if validation_manager and not args.skip_implicit_validation:
    initial_validation_result = validation_manager.Validate()
    if initial_validation_result and not initial_validation_result.success:
      raise RuntimeError(
          "Initial validation failed, aborting further operations.")

  registry = CreateCommandRegistry(
      file_access_policy,
      validation_manager,
      start_new_task=lambda task_info: CommandOutput(
          command_name="task",
          output="",
          errors="TaskCommand execution not implemented",
          summary="Not implemented"),
      git_dirty_accept=args.git_dirty_accept)

  conversation_factory = ConversationFactory(
      conversation_factory_options._replace(command_registry=registry))

  conversation_path = re.sub(r'\.txt$', '.conversation.json', args.task)
  conversation_name = os.path.basename(args.task).replace('.txt', '')

  confirmation_state = ConfirmationState(
      confirmation_manager=confirmation_manager,
      confirm_every=args.confirm_every)

  task_file_content: str = ""
  with open(args.task, 'r') as f:
    task_file_content = f.read()

  task_file_content += _read_prompt_include_files(args.prompt_include,
                                                  file_access_policy)

  conversation, start_message = LoadOrCreateConversation(
      task_file_content, args.task, conversation_factory, conversation_path,
      registry, file_access_policy, validation_manager, confirmation_state,
      conversation_name)

  return AgentLoopOptions(
      task_prompt_content=task_file_content,
      conversation_factory=conversation_factory,
      conversation=conversation,
      start_message=start_message,
      commands_registry=registry,
      confirmation_state=confirmation_state,
      file_access_policy=file_access_policy,
      conversational_ai=GetConversationalAI(args, registry),
      confirm_regex=confirm_regex,
      confirm_done=args.confirm,
      skip_implicit_validation=args.skip_implicit_validation,
      validation_manager=validation_manager,
      do_review=args.review,
      review_first=args.review_first,
  )


def LoadOrCreateConversation(
    task_file_content: str,
    task_file_path: str,
    conversation_factory: ConversationFactory,
    conversation_path: str,
    registry: CommandRegistry,
    file_access_policy: FileAccessPolicy,
    validation_manager: Optional[ValidationManager],
    confirmation_state: ConfirmationState,
    conversation_name: str,
) -> Tuple[Conversation, Message]:

  conversation = conversation_factory.New(
      name=conversation_name, path=conversation_path)
  if conversation.messages:
    next_message = Message(
        'system',
        content_sections=[
            ContentSection(
                content='The server running this interaction has been restarted.',
                summary=None)
        ])
  else:
    content_sections: List[ContentSection] = []

    agent_prompt_path = 'agent/prompt.txt'
    if os.path.exists(agent_prompt_path):
      with open(agent_prompt_path, 'r') as f:
        content_sections.append(
            ContentSection(
                content=f.read(),
                summary=f"Constant prompt guidance: {agent_prompt_path}"))

    content_sections.append(
        ContentSection(
            content=task_file_content,
            summary=f"Contents from --task file ({task_file_path})"))

    next_message = Message('system', content_sections=content_sections)

  return conversation, next_message


def CreateFileAccessPolicy(
    file_access_regex: Optional[str],
    file_access_regex_path: TrackedFlagStr) -> FileAccessPolicy:
  policies: List[FileAccessPolicy] = [CurrentDirectoryFileAccessPolicy()]

  if file_access_regex:
    if file_access_regex_path.set_explicitly:
      print(
          "Error: Invalid usage: "
          "At most one of `--file-access-regex` and `--file-access-regex-path` can be used.",
          file=sys.stderr)
      sys.exit(1)
  elif file_access_regex_path.value:
    try:
      with open(file_access_regex_path.value, 'r') as f:
        file_access_regex = f.read().strip()
      if not file_access_regex:
        print(
            f"Error: Invalid usage: --file-access-regex-path: "
            f"{file_access_regex_path.value}: File is empty.",
            file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
      if file_access_regex_path.set_explicitly:
        print(
            f"Error: --file-access-regex-path: {file_access_regex_path.value}: {e}",
            file=sys.stderr)
        sys.exit(1)

  if file_access_regex:
    policies.append(RegexFileAccessPolicy(file_access_regex))
  return CompositeFileAccessPolicy(policies)


def TestFileAccess(file_access_policy: FileAccessPolicy) -> None:
  for file in list_all_files('.', file_access_policy):
    print(file)


def _read_prompt_include_files(paths: List[str],
                               file_access_policy: FileAccessPolicy) -> str:
  not_allowed_paths = list(
      filter(lambda p: not file_access_policy.allow_access(os.path.abspath(p)),
             paths))
  if not_allowed_paths:
    print(
        "Error: --prompt-include: Access to the following included files not allowed by policy:",
        file=sys.stderr)
    for path in not_allowed_paths:
      print(f"  {path}", file=sys.stderr)
    sys.exit(1)

  output = []
  for included_file_path in paths:
    try:
      with open(included_file_path, 'r') as f:
        included_content = f.read()
      output.append(
          f"\n\n## Context file: {included_file_path}\n{included_content}")
    except FileNotFoundError:
      print(
          f"Error: --prompt-include: File not found: {included_file_path}",
          file=sys.stderr)
      sys.exit(1)
    except IOError as e:
      print(
          f"Error: --prompt-include: Error while reading {included_file_path}: {e}",
          file=sys.stderr)
      sys.exit(1)

  return ''.join(output)
