import chainlit as cl
from chainlit.cli import run_chainlit
import os
from pathology.path import Path

from py.backend.llm_providers.openai_provider import OpenAIProvider

script_dir = Path.script_dir()
root_dir = str((script_dir / '../../..').resolve())

os.chdir(root_dir)
from py.backend.engine.engine import Engine

# Define the tools directory
tools_dir = str((script_dir / '../../backend/tools').resolve())

default_model = "gpt-4o"
openai_provider = OpenAIProvider(
    os.environ['OPENAI_API_KEY'],
    default_model)

engine = Engine([openai_provider], default_model, tools_dir)


@cl.on_message
async def main(message: cl.Message):
    response = engine.send_message(message.content, default_model, None)
    await cl.Message(content=response).send()


@cl.on_chat_start
async def chat_start():
    welcome_msg = "AI-6 is ready 😊"
    await cl.Message(content=welcome_msg).send()


if __name__ == "__main__":
    target = str(script_dir / "app.py")
    run_chainlit(target)
