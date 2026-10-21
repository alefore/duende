#!/usr/bin/bash
set -e
PLAN_SOURCE=$HOME/coding-plan/src
export PYTHONPATH="$PLAN_SOURCE:$PYTHONPATH"

echo "<task>"
python3 $PLAN_SOURCE/main.py ls --task_format=full --task_count=1 --state_filter=pending --plan $DUENDE_AGENT_CWD/plan.md
echo "</task>"
