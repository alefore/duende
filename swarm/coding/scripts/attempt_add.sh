#!/usr/bin/bash
set -e
PLAN_SOURCE=$HOME/coding-plan/src
export PYTHONPATH="$PLAN_SOURCE:$PYTHONPATH"

$PYTHON $PLAN_SOURCE/main.py attempt_add
