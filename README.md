# Duende

Agent implementation for Conversational AI to modify a git-backed source code
repository.

## Dependencies

You need to install a few dependencies:

    pip install openai flask google-generativeai flask-socketio types-flask-socketio

## Basic usage

This instructions assume you have Duende at ~/duende.

1. Get a Gemini API key (see below). Let's assume this is ~/.gemini/api_key

2. Write a file with a task. See conversations/ for examples. Let's assume this
   is conversations/my-task.txt

3. Pick a model. Usually `gemini-2.5-flash` is good enough, but you may want to
   try with `gemini-2.5-pro`. Use `gemini-LIST` to get a list of available
   models.

4. Come up with a regex that matches all the files you want to expose (for both
   read and write access).

   You can test your regex thus:

   $ python3 ~/duende/src/agent_server.py --api-key ~/.gemini/api_key --task conversations/my-task.txt --model=gemini-2.5-pro --confirm=.* --file-access-test

## Optional features

## Using with Gemini

You need to get an API key and store it in a file that you can pass through `--api-key`.

TODO: Add instructions of how to get an API key.

## Usage

