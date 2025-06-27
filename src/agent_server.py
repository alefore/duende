import argparse
from flask import Flask, request
from flask_socketio import SocketIO
import logging
from typing import Any, Dict

from args_common import CreateCommonParser
from conversation import ConversationId
from web_server_state import WebServerState
from random_key import GenerateRandomKey

app = Flask(__name__)
app.config['SECRET_KEY'] = GenerateRandomKey(24)


def parse_arguments() -> argparse.Namespace:
  parser = CreateCommonParser()
  parser.add_argument(
      '--port', type=int, default=5000, help="Port to run the web server on.")
  return parser.parse_args()


@app.route("/", methods=["GET"])
def Interact() -> Any:
  return app.send_static_file('index.html')


def SendUpdate(server_state: WebServerState, data: Dict[str, Any]) -> None:
  message_count = data.get('message_count', 0)
  conversation_id = data.get('conversation_id')
  if conversation_id is None:
    logging.error("SendUpdate: conversation_id is missing")
    return

  logging.info(f"Received: request_update, message_count: {message_count}")
  server_state.SendUpdate(
      conversation_id, message_count, confirmation_required=None)


def run_server() -> None:
  args = parse_arguments()
  socketio = SocketIO(app)
  server_state = WebServerState(args, socketio)

  @socketio.on('confirm')
  def handle_confirmation(data: Dict[str, Any]) -> None:
    logging.info("Received: confirm.")
    confirmation = data.get('confirmation')
    if confirmation is None:
      logging.error("handle_confirmation: confirmation is missing")
      return
    server_state.ReceiveConfirmation(confirmation)
    SendUpdate(server_state, data)

  @socketio.on('request_update')
  def start_update(data: Dict[str, Any]) -> None:
    SendUpdate(server_state, data)

  @socketio.on('list_conversations')
  def list_conversations() -> None:
    logging.info("Received: list_conversations request")
    server_state.ListConversations()

  socketio.run(app, port=args.port)


if __name__ == "__main__":
  run_server()
