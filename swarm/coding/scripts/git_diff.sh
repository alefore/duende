#!/usr/bin/bash
cd $DUENDE_AGENT_CWD/repository
CHANGES=$(git diff)
if [ -n "$CHANGES" ]; then
  echo "Changes in repository/:"
  echo "$CHANGES"
else
  echo "repository/ has no changes."
fi
