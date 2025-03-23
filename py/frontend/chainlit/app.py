import asyncio

import chainlit as cl
from chainlit.cli import run_chainlit
import os
from openai import OpenAI
from pathology.path import Path

script_dir = Path.script_dir()
root_dir = str((script_dir / '../../..').resolve())

os.chdir(root_dir)
from py.backend.engine.engine import Engine

# Define the tools directory
tools_dir = str((script_dir / '../../backend/tools').resolve())

# Create an OpenAI client
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
model_name = "gpt-4o"

engine = Engine(client, model_name, tools_dir)


@cl.on_message
async def main(message: cl.Message):
    response = engine.send_message(message.content, None)
    await cl.Message(content=response).send()


@cl.on_chat_start
async def chat_start():
    welcome_msg = "AI-6 is ready 🚀"
    await cl.Message(content=welcome_msg).send()


if __name__ == "__main__":
    target = str(script_dir / "app.py")
    run_chainlit(target)
