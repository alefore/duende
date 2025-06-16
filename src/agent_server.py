import os
import argparse
from flask import Flask, request, render_template_string, redirect, url_for
from threading import Thread
import logging

from args_common import CreateCommonParser, CreateAgentLoopOptions
from agent_loop import LoadOpenAIAPIKey, AgentLoop
from confirmation import AsyncConfirmationManager

app = Flask(__name__)
agent_loop_instance = None
confirmation_manager = AsyncConfirmationManager()

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Agent Server</title>
  </head>
  <body>
    <h1>Agent Server Interface</h1>
    <form action="/" method="post">
      <textarea name="prompt" rows="4" cols="50" placeholder="Enter prompt..."></textarea><br>
      <input type="submit" value="Submit Prompt">
    </form>
    <h2>Confirmation</h2>
    <div>{{ confirmation_message or "No confirmation needed." }}</div>
    {% if confirmation_message %}
    <form action="/confirm" method="post">
      <input type="text" name="confirmation" placeholder="Enter confirmation..."><br>
      <input type="submit" value="Submit Confirmation">
    </form>
    {% endif %}
    <h2>Conversation</h2>
    <div style="white-space: pre-wrap;">{{ conversation }}</div>
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
      return redirect(url_for('interact'))

  conversation = "\n".join(f"{message['role']}: {message['content']}"
                           for message in agent_loop_instance.options.messages
                          ) if agent_loop_instance else "No conversation yet."

  confirmation_message = confirmation_manager.get_pending_message()
  return render_template_string(
      HTML_TEMPLATE,
      conversation=conversation,
      confirmation_message=confirmation_message)


@app.route("/confirm", methods=["POST"])
def confirm():
  global confirmation_manager
  confirmation = request.form.get("confirmation")
  confirmation_manager.provide_confirmation(confirmation)
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
  app.run(port=args.port)


if __name__ == "__main__":
  run_server()
