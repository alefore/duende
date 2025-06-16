import argparse
import logging
from agent_loop import LoadOpenAIAPIKey, AgentLoop
from args_common import CreateCommonParser, CreateAgentLoopOptions


def parse_arguments() -> argparse.Namespace:
  parser = CreateCommonParser()
  parser.add_argument(
      '--confirm_done',
      action='store_true',
      help="Require confirmation before executing the done command.")
  return parser.parse_args()


def main() -> None:
  args: argparse.Namespace = parse_arguments()

  LoadOpenAIAPIKey(args.api_key)

  try:
    options = CreateAgentLoopOptions(args)
  except RuntimeError as e:
    logging.error(e)
    return

  loop = AgentLoop(options)
  loop.run()


if __name__ == '__main__':
  main()
