#!/usr/bin/bash

exit_status=0

function run_command {
  local command="$1"
  local tmp_output
  tmp_output=$(mktemp)

  echo "Running: $command"
  if ! eval "$command" >"$tmp_output" 2>&1; then
    echo "Command failed: $command" >&2
    cat "$tmp_output" >&2
    exit_status=1
  fi

  rm -f "$tmp_output"
}

run_command "~/bin/mypy --strict src/agent_cli.py"
run_command "~/bin/mypy --strict src/agent_server.py"

for file in src/test_{args_common,async_confirmation_manager,command_registry,validate_command_input,write_file_command,agent_loop}.py; do
  run_command "${VALIDATE_PYTHON:-python3} $file"
done

exit $exit_status
