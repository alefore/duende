import argparse
import logging
from agent_loop import AgentLoop
from args_common import CreateCommonParser, CreateAgentLoopOptions
from confirmation import CLIConfirmationManager


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
    options = CreateAgentLoopOptions(args, CLIConfirmationManager())
  except RuntimeError as e:
    logging.error(e)
    return

  loop = AgentLoop(options)
  loop.run()


if __name__ == '__main__':
  main()
