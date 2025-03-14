#!/bin/bash

# Activate venv if not active already
if [[ -z "$VIRTUAL_ENV" || "$VIRTUAL_ENV" != *"ai-six/py/venv" ]]; then
  source py/venv/bin/activate
fi

python -m py.frontend.cli.ai6
