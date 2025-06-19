import os
import argparse
from flask import Flask, request
from flask_socketio import SocketIO, emit
from threading import Thread
import logging

from args_common import CreateCommonParser, CreateAgentLoopOptions
from agent_loop import LoadOpenAIAPIKey, AgentLoop
from confirmation import AsyncConfirmationManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
agent_loop_instance = None


def on_confirmation_requested(message: str) -> None:
  if agent_loop_instance:
    UpdatePage(agent_loop_instance, True)


confirmation_manager = AsyncConfirmationManager(on_confirmation_requested)

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Agent Server</title>
    <link rel=stylesheet href="/static/agent.css">
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="/static/agent.js"></script>
  </head>
  <body>
    <h1>Agent Server Interface</h1>
    <div id="conversation"></div>
    <div id="confirmation"></div>
    <form id="confirmation_form" style="display: block;">
      <input type="text" name="confirmation" placeholder="Confirmation…"><br>
      <input id="confirmButton" type="submit" value="Confirm">
    </form>
  </body>
</html>
"""


def parse_arguments() -> argparse.Namespace:
  parser = CreateCommonParser()
  parser.add_argument(
      '--port', type=int, default=5000, help="Port to run the web server on.")
  return parser.parse_args()


def UpdatePage(agent_loop: AgentLoop, confirmation_required: bool) -> None:
  logging.info(f"Computing data.")
  data = {
      'confirmation_required': confirmation_required,
      'conversation': agent_loop.options.messages
  }
  socketio.emit('update', data)


@app.route("/", methods=["GET"])
def interact():
  return HTML_TEMPLATE


def start_agent_loop(args: argparse.Namespace) -> None:
  global agent_loop_instance, confirmation_manager
  LoadOpenAIAPIKey(args.api_key)

  try:
    options = CreateAgentLoopOptions(args, confirmation_manager)
  except RuntimeError as e:
    logging.error(e)
    return

  agent_loop_instance = AgentLoop(options)
  Thread(target=agent_loop_instance.run).start()


def run_server() -> None:
  args = parse_arguments()
  start_agent_loop(args)

  @socketio.on('confirm')
  def handle_confirmation(data) -> None:
    logging.info("Received confirmation.")
    global agent_loop_instance, confirmation_manager
    if agent_loop_instance:
      UpdatePage(agent_loop_instance, False)
    confirmation_manager.provide_confirmation(data.get('confirmation'))

  @socketio.on('request_update')
  def start_update(data) -> None:
    logging.info("Received: request_update.")
    global agent_loop_instance, confirmation_manager
    if agent_loop_instance:
      UpdatePage(agent_loop_instance,
                 confirmation_manager.get_pending_message() is not None)
    else:
      logging.info("No agent loop instance!")

  socketio.run(app, port=args.port)


if __name__ == "__main__":
  run_server()
