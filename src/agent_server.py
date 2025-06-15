import os
from flask import Flask, request, render_template_string
from agent_loop import AgentLoop, CreateCommandRegistry, CreateFileAccessPolicy, LoadOrCreateConversation, LoadOpenAIAPIKey, CreateValidationManager
import logging
from threading import Thread

app = Flask(__name__)
agent_loop_instance = None

# Basic HTML template for displaying the conversation and a prompt input field
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
    <h2>Conversation</h2>
    <div style="white-space: pre-wrap;">{{ conversation }}</div>
  </body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def interact():
  global agent_loop_instance
  if request.method == "POST":
    prompt = request.form.get("prompt")
    if agent_loop_instance:
      agent_loop_instance.messages.append({'role': 'user', 'content': prompt})

  conversation = "\n".join(f"{message['role']}: {message['content']}"
                           for message in agent_loop_instance.messages
                          ) if agent_loop_instance else "No conversation yet."

  return render_template_string(HTML_TEMPLATE, conversation=conversation)


def start_agent_loop(args):
  global agent_loop_instance
  LoadOpenAIAPIKey(args.api_key)

  file_access_policy = CreateFileAccessPolicy(args)
  validation_manager = CreateValidationManager()

  if validation_manager:
    initial_validation_result = validation_manager.Validate()
    if initial_validation_result and initial_validation_result.returncode != 0:
      logging.error("Initial validation failed, aborting further operations.")
      return

  registry = CreateCommandRegistry(file_access_policy, validation_manager)
  messages, conversation_path = LoadOrCreateConversation(args.task, registry)

  agent_loop_instance = AgentLoop(args.model, messages, registry)
  Thread(target=agent_loop_instance.run).start()


def run_server(args):
  start_agent_loop(args)
  app.run(port=args.port)


if __name__ == "__main__":
  import argparse

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
  args = parser.parse_args()

  run_server(args)
