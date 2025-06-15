import os
import argparse
import re
from flask import Flask, request, render_template_string, redirect, url_for
from agent_loop import AgentLoop, CreateCommandRegistry, CreateFileAccessPolicy, LoadOrCreateConversation, LoadOpenAIAPIKey, CreateValidationManager
from confirmation import AsyncConfirmationManager
import logging
from threading import Thread

app = Flask(__name__)
agent_loop_instance = None
confirmation_manager = AsyncConfirmationManager()

# Basic HTML template for displaying the conversation, a confirmation message, and a prompt input field
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
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--port', type=int, default=5000, help="Port to run the web server on.")
  parser.add_argument(
      '--api_key', type=str, default=os.path.expanduser('~/.openai/api_key'))
  parser.add_argument(
      '--task', type=str, required=True, help="File path for task prompt.")
  parser.add_argument(
      '--model',
      type=str,
      default='gpt-4o',
      help="The model name to use for OpenAI API requests.")
  parser.add_argument(
      '--file_access_regex',
      type=str,
      help="Regex to match allowed file paths. Defaults to allowing all paths.")
  parser.add_argument(
      '--confirm_regexp',
      type=str,
      help="Regex pattern to determine which operations require confirmation.")
  return parser.parse_args()


@app.route("/", methods=["GET", "POST"])
def interact():
  global agent_loop_instance, confirmation_manager
  if request.method == "POST":
    prompt = request.form.get("prompt")
    if agent_loop_instance:
      agent_loop_instance.messages.append({'role': 'user', 'content': prompt})
      return redirect(url_for('interact'))

  conversation = "\n".join(f"{message['role']}: {message['content']}"
                           for message in agent_loop_instance.messages
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
  if confirmation:
    confirmation_manager.provide_confirmation(confirmation)
  return redirect(url_for('interact'))


def start_agent_loop(args: argparse.Namespace) -> None:
  global agent_loop_instance, confirmation_manager
  LoadOpenAIAPIKey(args.api_key)

  file_access_policy = CreateFileAccessPolicy(args.file_access_regex)
  validation_manager = CreateValidationManager()

  if validation_manager:
    initial_validation_result = validation_manager.Validate()
    if initial_validation_result and initial_validation_result.returncode != 0:
      logging.error("Initial validation failed, aborting further operations.")
      return

  registry = CreateCommandRegistry(file_access_policy, validation_manager)
  messages, conversation_path = LoadOrCreateConversation(args.task, registry)

  confirm_regex = re.compile(
      args.confirm_regexp) if args.confirm_regexp else None

  agent_loop_instance = AgentLoop(
      args.model,
      messages,
      registry,
      confirm_regex,  # Use the confirm_regex from args
      False,  # Default for confirm_done
      confirmation_manager)
  Thread(target=agent_loop_instance.run).start()


def run_server():
  args = parse_arguments()
  start_agent_loop(args)
  app.run(port=args.port)


if __name__ == "__main__":
  run_server()
