import argparse
import logging
import os
import re
import sys
from typing import Optional, Pattern, List, Tuple, Callable
from agent_loop import AgentLoopOptions
from confirmation import ConfirmationState, ConfirmationManager, CLIConfirmationManager
from file_access_policy import FileAccessPolicy, RegexFileAccessPolicy, CurrentDirectoryFileAccessPolicy, CompositeFileAccessPolicy
from list_files import list_all_files
from command_registry import CommandRegistry, CreateCommandRegistry
from validation import CreateValidationManager, ValidationManager
from task_command import CommandOutput, TaskInformation
from chatgpt import ChatGPT
from conversation import Conversation, ConversationFactory, Message, MultilineContent
from conversational_ai import ConversationalAI
from gemini import Gemini
from parsing import ExtractCommands
from validate_command_input import ValidateCommandInput


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
  parser.add_argument(
      '--git-dirty-accept',
      action='store_true',
      default=False,
      help="Allow the program to proceed even if the Git repository has uncommitted changes."
  )
  parser.add_argument(
      '--review',
      action='store_true',
      help="Trigger an AI review of changes when the agent loop issues the #done command. The review happens in a new conversation."
  )
  return parser


def GetConversationalAI(args: argparse.Namespace) -> ConversationalAI:
  if args.model.startswith('gpt'):
    return ChatGPT(args.api_key, args.model)
  if args.model.startswith('gemini'):
    return Gemini(args.api_key, args.model)
  raise Exception(f"Unknown AI: {args.model}")


def CreateAgentLoopOptions(args: argparse.Namespace,
                           confirmation_manager: ConfirmationManager,
                           conversation_factory) -> AgentLoopOptions:
  file_access_policy = CreateFileAccessPolicy(args.file_access_regex)

  matched_files = list(list_all_files('.', file_access_policy))
  logging.info(f"File matched by access policy: {len(matched_files)}")
  if not matched_files:
    print("No files match the given file access policy. Aborting execution.")
    sys.exit(1)

  if args.test_file_access:
    TestFileAccess(file_access_policy)
    sys.exit(0)

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
          summary="Not implemented"),
      git_dirty_accept=args.git_dirty_accept)

  conversation_path = re.sub(r'\.txt$', '.conversation.json', args.task)

  confirmation_state = ConfirmationState(
      confirmation_manager=confirmation_manager,
      confirm_every=args.confirm_every)

  original_task_file_content: List[str] = []
  with open(args.task, 'r') as f:
    original_task_file_content = [l.rstrip() for l in f.readlines()]

  conversation, start_message = LoadOrCreateConversation(
      original_task_file_content, conversation_factory, conversation_path,
      registry, file_access_policy, validation_manager, confirmation_state)

  return AgentLoopOptions(
      conversation_factory=conversation_factory,
      conversation_path=conversation_path,
      model=args.model,
      conversation=conversation,
      start_message=start_message,
      commands_registry=registry,
      confirmation_state=confirmation_state,
      file_access_policy=file_access_policy,
      conversational_ai=GetConversationalAI(args),
      confirm_regex=confirm_regex,
      confirm_done=args.confirm,
      skip_implicit_validation=args.skip_implicit_validation,
      validation_manager=validation_manager,
      do_review=args.review,
      original_task_prompt_content=original_task_file_content,
  )


def LoadOrCreateConversation(
    task_file_content: List[str],
    conversation_factory: ConversationFactory,
    conversation_path: str,
    registry: CommandRegistry,
    file_access_policy: FileAccessPolicy,
    validation_manager: Optional[ValidationManager],
    confirmation_state: ConfirmationState,
) -> Tuple[Conversation, Message]:

  conversation = conversation_factory.Load(conversation_path)
  if conversation.messages:
    next_message = Message(
        'system',
        content_sections=[[
            'The server running this interaction has been restarted.'
        ]])
  else:
    content_sections: List[MultilineContent] = []

    content_sections.append([
        "You are a coding assistant operating in a command loop environment. "
        "Send in your response commands prefixed with `#`. "
        "I will execute those commands and tell you the results. "
        "Do not hallucinate results on your own. "
        "Anything that is not a command will be relayed to the human."
    ])

    agent_prompt_path = 'agent/prompt.txt'
    if os.path.exists(agent_prompt_path):
      with open(agent_prompt_path, 'r') as f:
        content_sections.append(list(l.rstrip() for l in f.readlines()))

    commands_from_task, non_command_lines = ExtractCommands(
        '\n'.join(task_file_content))

    if non_command_lines:
      content_sections.append(non_command_lines)

    if commands_from_task:
      for cmd_input in commands_from_task:
        if cmd_input.command_name == "done":
          logging.error(f"Task file: #done command found in initial task file.")
          sys.exit(1)

        command = registry.Get(cmd_input.command_name)
        if not command:
          logging.error(
              f"Task file: Error: Unknown command '{cmd_input.command_name}' found in task file. Aborting execution."
          )
          sys.exit(1)

        warnings = ValidateCommandInput(command.Syntax(), cmd_input,
                                        file_access_policy)
        if warnings:
          for warning in warnings:
            logging.error(
                f"Task file: Error validating command '{cmd_input.command_name}' from task file: {warning}. Aborting execution."
            )
            sys.exit(1)

        command_output = command.Execute(cmd_input)
        if command_output.errors:
          for error in command_output.errors:
            logging.error(
                f"Task file: Error '#{cmd_input.command_name}': {error}.")
            sys.exit(1)
        if command_output.output:
          content_sections.append(command_output.output)

    content_sections.append([
        'Some commands accept multi-line information, like this:',
        '',
        '#write_file foo.py <<',
        'line0',
        'line1',
        '…',
        '#end',
        'When you\'re done (or if you get stuck), '
        'issue #done to notify the human and stop this conversation.',
        '',
        'Anything sent outside of commands will be treated as plain text.',
        'You can send many commands per message. '
        'For example, if you want to read 5 files, '
        'you can issue 5 #read_file commands at once.',
        '',
        'Available commands:',
    ])
    content_sections[-1].append(registry.HelpText())
    next_message = Message('system', content_sections=content_sections)

  return conversation, next_message


def CreateFileAccessPolicy(
    file_access_regex: Optional[str]) -> FileAccessPolicy:
  policies: List[FileAccessPolicy] = [CurrentDirectoryFileAccessPolicy()]
  if file_access_regex:
    policies.append(RegexFileAccessPolicy(file_access_regex))
  return CompositeFileAccessPolicy(policies)


def TestFileAccess(file_access_policy: FileAccessPolicy):
  for file in list_all_files('.', file_access_policy):
    print(file)
