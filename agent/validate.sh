#!/usr/bin/bash
~/bin/mypy src/agent_loop.py >&2
python3 src/test_select_commands.py
