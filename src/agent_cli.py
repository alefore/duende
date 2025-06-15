import argparse
import logging
import re
from typing import Optional, Pattern
from agent_loop import (ParseArguments, LoadOpenAIAPIKey,
                        CreateFileAccessPolicy, TestFileAccess,
                        CreateValidationManager, CreateCommandRegistry,
                        LoadOrCreateConversation, AgentLoop, CommandRegistry,
                        ValidationManager)
from file_access_policy import FileAccessPolicy


def main() -> None:
  args: argparse.Namespace = ParseArguments()

  LoadOpenAIAPIKey(args.api_key)

  file_access_policy: FileAccessPolicy = CreateFileAccessPolicy(args)

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
