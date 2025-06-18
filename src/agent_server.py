import os
import argparse
from flask import Flask, request, render_template_string, redirect, url_for
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
  socketio.emit('update_confirmation', {'confirmation_message': message})


confirmation_manager = AsyncConfirmationManager(on_confirmation_requested)

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Agent Server</title>
    <style>
      body {
        overflow-y: scroll; /* Always show vertical scrollbar */
      }
    </style>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script>
      document.addEventListener("DOMContentLoaded", function() {
        var socket = io();
        socket.on("update_conversation", function(data) {
          document.getElementById('conversation').innerText = data.conversation;
          scrollToBottom();
        });
        socket.on("update_confirmation", function(data) {
          document.getElementById('confirmation').innerText = data.confirmation_message || "No confirmation needed.";
          var confirmationForm = document.getElementById('confirmation_form');
          if (data.confirmation_message) {
            confirmationForm.style.display = 'block';
          } else {
            confirmationForm.style.display = 'none';
          }
          scrollToBottom();
        });

        function scrollToBottom() {
          window.scrollTo(0, document.body.scrollHeight);
        }
      });
    </script>
  </head>
  <body>
    <h1>Agent Server Interface</h1>
    <form action="/" method="post">
      <textarea name="prompt" rows="4" cols="50" placeholder="Enter prompt..."></textarea><br>
      <input type="submit" value="Submit Prompt">
    </form>
    <h2>Conversation</h2>
    <div id="conversation" style="white-space: pre-wrap;">{{ conversation }}</div>
    <h2>Confirmation</h2>
    <div id="confirmation">{{ confirmation_message or "No confirmation needed." }}</div>
    <form id="confirmation_form" action="/confirm" method="post" style="display: {{ 'block' if confirmation_message else 'none' }};">
      <input type="text" name="confirmation" placeholder="Enter confirmation..."><br>
      <input type="submit" value="Submit Confirmation">
    </form>
  </body>
</html>
"""


def parse_arguments() -> argparse.Namespace:
  parser = CreateCommonParser()
  parser.add_argument(
      '--port', type=int, default=5000, help="Port to run the web server on.")
  return parser.parse_args()


@app.route("/", methods=["GET", "POST"])
def interact():
  global agent_loop_instance, confirmation_manager
  if request.method == "POST":
    prompt = request.form.get("prompt")
    if agent_loop_instance:
      agent_loop_instance.options.messages.append({
          'role': 'user',
          'content': prompt
      })
      socketio.emit(
          'update_conversation', {
              'conversation':
                  "\n".join(f"{message['role']}: {message['content']}"
                            for message in agent_loop_instance.options.messages)
          })

  conversation = "\n".join(f"{message['role']}: {message['content']}"
                           for message in agent_loop_instance.options.messages
                          ) if agent_loop_instance else "No conversation yet."

  confirmation_message = confirmation_manager.get_pending_message()
  socketio.emit('update_confirmation',
                {'confirmation_message': confirmation_message})
  return render_template_string(
      HTML_TEMPLATE,
      conversation=conversation,
      confirmation_message=confirmation_message)


@app.route("/confirm", methods=["POST"])
def confirm():
  global confirmation_manager
  confirmation = request.form.get("confirmation")
  confirmation_manager.provide_confirmation(confirmation)
  socketio.emit(
      'update_confirmation',
      {'confirmation_message': confirmation_manager.get_pending_message()})
  return redirect(url_for('interact'))


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


def run_server():
  args = parse_arguments()
  start_agent_loop(args)
  socketio.run(app, port=args.port)


if __name__ == "__main__":
  run_server()
