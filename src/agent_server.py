import argparse
from flask import Flask, request
from flask_socketio import SocketIO
import logging

from args_common import CreateCommonParser
from web_server_state import WebServerState
from random_key import GenerateRandomKey

app = Flask(__name__)
app.config['SECRET_KEY'] = GenerateRandomKey(24)

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
    <div id="automatic_confirmation_toggle">
      <label for="auto_confirm_checkbox">
        <input type="checkbox" id="auto_confirm_checkbox"> Automatic confirmation
      </label>
    </div>
    <div id="conversation"></div>
    <div id="confirmation"></div>
    <form id="confirmation_form" style="display: block;">
      <textarea name="confirmation" id="confirmation_input" placeholder="Confirmation…" autofocus rows="1"></textarea>
    </form>
  </body>
</html>
"""


def parse_arguments() -> argparse.Namespace:
  parser = CreateCommonParser()
  parser.add_argument(
      '--port', type=int, default=5000, help="Port to run the web server on.")
  return parser.parse_args()


@app.route("/", methods=["GET"])
def interact():
  return HTML_TEMPLATE


def SendUpdate(server_state, data):
  message_count = data.get('message_count', 0)
  logging.info(f"Received: request_update, message_count: {message_count}")
  server_state.SendUpdate(message_count, confirmation_required=None)


def run_server() -> None:
  args = parse_arguments()
  socketio = SocketIO(app)
  server_state = WebServerState(args, socketio)

  @socketio.on('confirm')
  def handle_confirmation(data) -> None:
    logging.info("Received: confirm.")
    server_state.ReceiveConfirmation(data.get('confirmation'))
    SendUpdate(server_state, data)

  @socketio.on('request_update')
  def start_update(data) -> None:
    SendUpdate(server_state, data)

  socketio.run(app, port=args.port)


if __name__ == "__main__":
  run_server()
