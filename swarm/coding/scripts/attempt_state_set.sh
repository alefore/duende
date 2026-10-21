#!/usr/bin/bash
set -e
PLAN_SOURCE=$HOME/coding-plan/src
export PYTHONPATH="$PLAN_SOURCE:$PYTHONPATH"

$PYTHON $PLAN_SOURCE/main.py state_set --target_state "$1" --attempt_details "$2" --attempt_title "$3"
