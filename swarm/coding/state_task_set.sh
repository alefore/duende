#!/usr/bin/bash
set -e
if [[ $# -ne 1 ]]; then
  echo "Usage: $(basename "$0"): state"
  exit 1
fi

: "${DUENDE_AGENT_CWD:?Error: Not set.}"
PLAN_PATH="$HOME/coding-plan/src"
export PYTHONPATH="$PYTHONPATH:$PLAN_PATH"

echo "<task>"
python3 $PLAN_PATH/main.py state_set --plan $DUENDE_AGENT_CWD/plan.md --target_state $1
echo "</task>"
