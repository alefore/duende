# Duende

Agent implementation for Conversational AI
to modify a git-backed source code repository.

![Duende Screenshot](/doc/duende.png?raw=true "Duende Screenshot")

## Dependencies

You need to install a few dependencies:

    pip install openai flask google-generativeai flask-socketio types-flask-socketio

## Basic usage

This instructions assume you have Duende at `~/duende`.

1. Get a Gemini API key (see below).
   Let's assume this is `~/.gemini/api_key`.
   Obviously, you should not commit it to your git repository.

2. Write a file with a task for the conversational AI.
   See conversations/ for examples.
   Let's assume this is `conversations/my-task.txt`

3. Pick a model.
   Usually `gemini-2.5-flash` is good enough,
   but you may want to try with `gemini-2.5-pro` (more expensive).
   Use `gemini-LIST` to get a list of available models.

4. Come up with a regex that matches all the files you want to expose
   (for both read and write access).
   Write it in: `agent/file-access-regex.txt`
   ([example](https://github.com/alefore/duende/blob/main/agent/file-access-regex.txt)).

   You can test your regex thus:

   $ python3 ~/duende/src/agent_server.py --task /dev/null --test-file-access

   (You can also specify the regex directly
   through command-line flag `--file-access-regex`,
   but I find this cumbersome.)

5. Run the server:

   $ python3 ~/duende/src/agent_server.py --task conversations/my-task.txt --confirm=.* --api-key ~/.gemini/api_key --model=gemini-2.5-flash --port 6785

6. Load the main web view:

   http://localhost:6785/

   Given the `--confirm` value,
   you will have to explicitly confirm that the conversation may proceed
   after each response from the AI.
   You do this by clicking on the "Confirmation…" box at the bottom
   and pressing return;
   you could type any instructions there and they will be relayed to the AI
   on the next response
   (which will also include the outputs of any commands by the AI).

## Additional features

### Constant context

You can create a file `agent/prompt.txt` with general context.
It will be included in all prompts.

### Validation

Having a strong suit of tests significantly raises the probability of success.
To do this, write a script `agent/validate.sh`.
It should compile your code (if applicable) and run all unit tests.

When found, Duende will expose a `validate` MCP command to the AI.
It will also start running this whenever the AI changes any files,
to inform the AI if things became broken (or fixed).

### Reviews

You can create a series of review "evaluators" in files matching
`agent/review/…/prompt.txt`
([examples](https://github.com/alefore/duende/tree/main/agent/review)).
In my experience, each evaluator should focus on a single well-defined check.

If you pass the `--review` command line argument,
when the main AI confirms that it is done applying the change,
Duende will spawn a separate conversation for each evaluator.
The evaluator will either accept or reject the change.

If any evaluator rejects the change, the main conversation will resume,
receiving the output of any evaluators that rejected the change.
