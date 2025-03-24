#!/bin/bash

# Activate venv if not active already
if [[ -z "$VIRTUAL_ENV" || "$VIRTUAL_ENV" != *"ai-six/py/venv" ]]; then
  source py/venv/bin/activate
fi

echo "virtualenv: ${VIRTUAL_ENV}"

if [[ "$1" == "cli" ]]; then
  python -m py.frontend.cli.ai6
elif [[ "$1" == "slack" ]]; then
  python -m py.frontend.slack.app
elif [[ "$1" == "chainlit" ]]; then
  python -m py.frontend.chainlit.app
else
  echo 'Usage: ai6.sh <cli | slack | chainlit>'
fi
