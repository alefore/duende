#!/usr/bin/bash
dir="$DUENDE_AGENT_CWD/research/"
FILES=$(ls $dir/*)
if [ -n "$FILES" ]; then
  echo "Research files available:"
  echo "$FILES"
else
  echo "No previous research files found."
fi
