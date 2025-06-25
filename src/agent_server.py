import argparse
from flask import Flask, request
from flask_socketio import SocketIO
import logging

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
def Interact():
  return app.send_static_file('index.html')


def SendUpdate(server_state, data) -> None:
  message_count = data.get('message_count', 0)
  logging.info(f"Received: request_update, message_count: {message_count}")
  server_state.SendUpdate(
      data.get('conversation_id'), message_count, confirmation_required=None)


def run_server() -> None:
  args = parse_arguments()
  socketio = SocketIO(app)
  server_state = WebServerState(args, socketio)

  @socketio.on('confirm')
  def handle_confirmation(data) -> None:
    logging.info("Received: confirm.")
    conversation_id = data.get('conversation_id')
    server_state.ReceiveConfirmation(data.get('confirmation'))
    SendUpdate(server_state, data)

  @socketio.on('request_update')
  def start_update(data) -> None:
    SendUpdate(server_state, data)

  socketio.run(app, port=args.port)


if __name__ == "__main__":
  run_server()
