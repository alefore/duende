import argparse
import logging
import os
import re
import sys
from typing import Optional, Pattern, List, Tuple, Callable
from agent_loop_options import AgentLoopOptions
from confirmation import ConfirmationState, ConfirmationManager, CLIConfirmationManager
from file_access_policy import FileAccessPolicy, RegexFileAccessPolicy, CurrentDirectoryFileAccessPolicy, CompositeFileAccessPolicy
from list_files import list_all_files
from command_registry import CommandRegistry
from command_registry_factory import CreateCommandRegistry
from validation import CreateValidationManager, ValidationManager
from agent_command import CommandOutput
from chatgpt import ChatGPT
from conversation import Conversation, ConversationFactory, Message, MultilineContent, ContentSection
from conversational_ai import ConversationalAI
from gemini import Gemini
from parsing import ExtractCommands
from validate_command_input import ValidateCommandInput


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
    conversation_factory: ConversationFactory) -> AgentLoopOptions:
  file_access_policy = CreateFileAccessPolicy(args.file_access_regex)

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
          output=[],
          errors=["TaskCommand execution not implemented"],
          summary="Not implemented"),
      git_dirty_accept=args.git_dirty_accept)

  conversation_path = re.sub(r'\.txt$', '.conversation.json', args.task)
  conversation_name = os.path.basename(args.task).replace('.txt', '')

  confirmation_state = ConfirmationState(
      confirmation_manager=confirmation_manager,
      confirm_every=args.confirm_every)

  task_file_content: List[str] = []
  with open(args.task, 'r') as f:
    task_file_content = [l.rstrip() for l in f.readlines()]

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
    task_file_content: List[str],
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
                content=[
                    'The server running this interaction has been restarted.'
                ],
                summary=None)
        ])
  else:
    content_sections: List[ContentSection] = []

    agent_prompt_path = 'agent/prompt.txt'
    if os.path.exists(agent_prompt_path):
      with open(agent_prompt_path, 'r') as f:
        content_sections.append(
            ContentSection(
                content=list(l.rstrip() for l in f.readlines()),
                summary=f"Constant prompt guidance: {agent_prompt_path}"))

    content_sections.append(
        ContentSection(
            content=task_file_content,
            summary=f"Contents from --task file ({task_file_path})"))

    next_message = Message('system', content_sections=content_sections)

  return conversation, next_message


def CreateFileAccessPolicy(
    file_access_regex: Optional[str]) -> FileAccessPolicy:
  policies: List[FileAccessPolicy] = [CurrentDirectoryFileAccessPolicy()]
  if file_access_regex:
    policies.append(RegexFileAccessPolicy(file_access_regex))
  return CompositeFileAccessPolicy(policies)


def TestFileAccess(file_access_policy: FileAccessPolicy) -> None:
  for file in list_all_files('.', file_access_policy):
    print(file)
