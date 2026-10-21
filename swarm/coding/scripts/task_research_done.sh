#!/usr/bin/bash
set -e
PLAN_SOURCE=$HOME/coding-plan/src
export PYTHONPATH="$PLAN_SOURCE:$PYTHONPATH"

RESEARCH_PATH=$1

if [ ! -f "$RESEARCH_PATH" ]; then
  echo "Error: File missing: $RESEARCH_PATH"
  exit 1
fi

if [[ ! "$RESEARCH_PATH" =~ ^research/[^/]+$ ]]; then
  echo "Error: Invalid path: $RESEARCH_PATH"
  exit 1
fi

$PYTHON $PLAN_SOURCE/main.py state_set --target_state "Success" --attempt_title "$RESEARCH_PATH"
