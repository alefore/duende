#!/usr/bin/bash
set -e
PLAN_SOURCE=$HOME/coding-plan/src
export PYTHONPATH="$PLAN_SOURCE:$PYTHONPATH"

python3 $PLAN_SOURCE/main.py task_add --title=$1 --description=$2 --plan $DUENDE_AGENT_CWD/plan.md
echo "Task added: $1"
