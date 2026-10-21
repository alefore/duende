#!/usr/bin/bash

: "${DUENDE_AGENT_CWD:?Error: Not set.}"
PLAN_PATH="$HOME/coding-plan/src"
export PYTHONPATH="$PYTHONPATH:$PLAN_PATH"

echo "<task>"
python3 $PLAN_PATH/main.py state_set --plan $DUENDE_AGENT_CWD/plan.md -h
echo "</task>"
