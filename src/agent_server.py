import argparse
from flask import Flask, request
from flask_socketio import SocketIO
import logging

from args_common import CreateCommonParser
from agent_loop import LoadOpenAIAPIKey
from web_server_state import WebServerState

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

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


@app.route("/", methods=["GET"])
def interact():
  return HTML_TEMPLATE


def run_server() -> None:
  args = parse_arguments()
  LoadOpenAIAPIKey(args.api_key)
  socketio = SocketIO(app)
  server_state = WebServerState(args, socketio)

  @socketio.on('confirm')
  def handle_confirmation(data) -> None:
    logging.info("Received: confirm.")
    server_state.ReceiveConfirmation(data.get('confirmation'))

  @socketio.on('request_update')
  def start_update(data) -> None:
    logging.info("Received: request_update.")
    server_state.SendUpdate(None)

  socketio.run(app, port=args.port)


if __name__ == "__main__":
  run_server()
