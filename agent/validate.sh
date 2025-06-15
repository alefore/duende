#!/usr/bin/bash
~/bin/mypy src/agent_loop.py >&2
for file in src/test_*.py; do
  echo "Tests: $file" >&2
  python3 $file
done