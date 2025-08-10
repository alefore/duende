# Duende

Duende is a Python/JS program providing a web-based interface
designed to enable you to guide a conversational AI (such as Gemini)
as it uses MCP to modify a source code repository
following your instructions.

You provide a task specifying requirements for the AI;
Duende starts a conversation and allows you to provide guidance
and observe all interactions.

It supports multiple workflows besides a single conversation.
Currently, the only additional workflow implemented is a `--review` mode,
where multiple review conversations are spawned
when the original conversation is done;
relevant feedback from the review conversations
is feed back to the main conversation.

![Duende Screenshot](/doc/duende.png?raw=true "Duende Screenshot")

## Quick Start

1.  **Install Dependencies:**
    ```bash
    pip install openai google-generativeai uvicorn fastapi
    ```

2.  **Get an API Key:** Obtain an API key from either OpenAI or Google Gemini and save it to a file. For example, `~/.gemini/api_key`.
    Currently only Gemini is supported
    (the integration with OpenAI is currently broken).

3.  **Define a Task:** Create a text file outlining the task for the AI. For example, `conversations/my-task.txt`
    (see [examples](https://github.com/alefore/duende/tree/main/conversations)).

4.  **Configure File Access:** Create a file named `agent/file-access-regex.txt` and add a regex that matches the files you want the AI to have access to.

5.  **Run the Server:**
    ```bash
    python3 src/agent_server.py \
        --task conversations/my-task.txt \
        --api-key ~/.gemini/api_key \
        --model gemini-2.5-flash \
        --port 6785
    ```

6.  **Open the Web UI:** Navigate to `http://localhost:6785/` in your browser to interact with the agent.

## Installation

Duende is written in Python 3. To install the required dependencies, run the following command:

```bash
pip install openai flask google-generativeai flask-socketio types-flask-socketio
```

## Configuration

### API Keys

Duende supports both **OpenAI** and **Google Gemini** models.
You will need to provide an API key for the service you wish to use.

You specify the path to your API key with the `--api-key` command-line argument.

### File Access

To prevent the AI from accessing sensitive files,
you must define a file access policy.
You can do this in one of two ways:

1.  **Regex File (Recommended):** Create a file at `agent/file-access-regex.txt` (or a custom path with `--file-access-regex-path`) containing a regex that matches the files the AI should be able to access.

2.  **Command-Line Flag:** Use the `--file-access-regex` flag to provide a regex directly on the command line.

You can test your file access configuration by running:
```bash
python3 src/agent_server.py --task /dev/null --test-file-access
```

Duende will only give the AI access to files in the local directory.

## Usage

The primary entry point for Duende is `src/agent_server.py`. Here is a typical command to run the agent:

```bash
python3 src/agent_server.py \
    --task conversations/my-task.txt \
    --api-key ~/.gemini/api_key \
    --model gemini-2.5-flash \
    --port 6785 \
    --confirm ".*"
```

Once the server is running, you can open the web interface at `http://localhost:6785/` to monitor and interact with the AI. The `--confirm ".*"` flag requires you to manually approve each action the AI takes.

### Command-Line Arguments

| Argument                     | Description                                                                                               | Default Value                |
| ---------------------------- | --------------------------------------------------------------------------------------------------------- | ---------------------------- |
| `--api-key`                  | Path to your API key file.                                                                                | `~/.openai/api_key`          |
| `--task`                     | **Required.** Path to the file containing the task prompt.                                                |                              |
| `--model`                    | The model name to use (e.g., `gpt-4o`, `gemini-2.5-pro`). Use `gemini-LIST` to list Gemini models.           | `gpt-4o`                     |
| `--file-access-regex`        | A regex to match allowed file paths.                                                                      |                              |
| `--file-access-regex-path`   | Path to a file containing a regex for file access.                                                        | `agent/file-access-regex.txt`|
| `--test-file-access`         | Tests the file access policy by listing all matched files and then exits.                                 |                              |
| `--confirm`                  | A regex to match commands that require user confirmation before execution.                                | `''`                         |
| `--confirm-every`            | Requires confirmation after every N interactions with the AI.                                             |                              |
| `--skip-implicit-validation` | Disables automatic validation after each AI interaction.                                                  | `False`                      |
| `--git-dirty-accept`         | Allows the program to run even if the Git repository has uncommitted changes.                             | `False`                      |
| `--review`                   | Triggers an AI review of the changes after the main task is completed.                                    | `False`                      |
| `--review-first`             | Triggers an AI review of the codebase *before* the main task begins.                                      | `False`                      |
| `--prompt-include`           | Path to a file to include in the prompt. Can be specified multiple times.                                 | `[]`                         |
| `--evaluate-evaluators`      | Runs tests to evaluate the performance of AI review evaluators.                                           | `False`                      |

## Advanced Features

### Constant Context

You can provide general context or instructions that will be included in every prompt by creating a file at `agent/prompt.txt`.

### Validation

You can create a validation script at `agent/validate.sh`.
This script should compile your code (if necessary) and run all tests.
The script should exit with 0 iff it succeeds
(in which case its stdout and stderr output will be ignored).
If it fails (exits with non-zero status),
it should print to stdout or stderr diagnostics information
to be sent to the AI.

When this script is present, Duende will:

1.  Expose a `validate` command to the AI.
2.  Automatically run the script whenever the AI modifies a file, providing immediate feedback on whether the changes introduced errors.

This greatly increases the probability that the AI will succeed in your task,
by providing a feedback loop.

See an example here: https://github.com/alefore/duende/blob/main/agent/validate.sh

### Reviews

Duende supports an automated review process.
You can create one or more review "evaluators" in files matching `agent/review/…/prompt.txt`.
Each evaluator should focus on a single, well-defined check.

If you pass the `--review` flag, a separate conversation will be spawned for each evaluator after the main task is complete.
If any evaluator rejects the change, the main conversation will resume with the feedback from the rejecting evaluators.

You can see examples here: https://github.com/alefore/duende/tree/main/agent/review

## Troubleshooting

*   **No files match the given file access policy:**
    This error means your regex in `agent/file-access-regex.txt` or `--file-access-regex` did not match any files.
    Use the `--test-file-access` flag to debug your regex.

*   **Initial validation failed:**
    This means your `agent/validate.sh` script exited with an error.
    Ensure your project's tests are passing before running the agent
    or use the command line flag `--skip-implicit-validation`.

*   **The repository has uncommitted changes:**
    This means that the local repository has uncommitted changes
    at start up (of the Duende process).
    Make sure to commit any previous changes
    or disable this check with `--git-dirty-accept`.
