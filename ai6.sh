#!/bin/bash

# Activate venv if not active already
if [[ -z "$VIRTUAL_ENV" || "$VIRTUAL_ENV" != *"ai-six/py/venv" ]]; then
  source py/venv/bin/activate
fi

if [[ "$1" == "cli" ]]; then
  python -m py.frontend.cli.ai6
elif [[ "$1" == "slack" ]]; then
  python -m py.frontend.slack.app
elif [[ "$1" == "chainlit" ]]; then
  python py/frontend/chainlit/app.py
else
  echo 'Usage: ai6.sh <cli | slack | chainlit>'
fi
