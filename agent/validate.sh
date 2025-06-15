#!/usr/bin/bash
set -e
~/bin/mypy src/agent_cli.py >&2
~/bin/mypy src/agent_server.py >&2
for file in src/test_*.py; do
  echo "Tests: $file" >&2
  python3 $file
done