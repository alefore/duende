import argparse
import logging
from agent_workflow import AgentWorkflow
from args_common import CreateCommonParser, CreateAgentWorkflow
from confirmation import CLIConfirmationManager
from conversation import ConversationFactory, ConversationFactoryOptions


def parse_arguments() -> argparse.Namespace:
  parser = CreateCommonParser()
  parser.add_argument(
      '--confirm_done',
      action='store_true',
      help="Require confirmation before executing the done command.")
  return parser.parse_args()


def main() -> None:
  args: argparse.Namespace = parse_arguments()

  try:
    workflow = CreateAgentWorkflow(args, CLIConfirmationManager(),
                                   ConversationFactoryOptions())
  except RuntimeError as e:
    logging.error(e)
    return

  workflow.run()


if __name__ == '__main__':
  main()
