#!/usr/bin/bash
set -e
PLAN_SOURCE=$HOME/coding-plan/src
export PYTHONPATH="$PLAN_SOURCE:$PYTHONPATH"

echo "<project>"
echo "<goal>"
python3 $PLAN_SOURCE/main.py goal --plan $DUENDE_AGENT_CWD/plan.md
echo "</goal>"

echo "<tasks>"
python3 $PLAN_SOURCE/main.py ls --task_format=llm_summary --plan $DUENDE_AGENT_CWD/plan.md
echo "</tasks>"
echo "</project>"
