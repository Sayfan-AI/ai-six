import os
from pathlib import Path

import chainlit as cl
from chainlit.cli import run_chainlit
from dotenv import load_dotenv

import pathology.path

from py.frontend.common import engine_utils

load_dotenv()

script_dir = pathology.path.Path.script_dir()

# Load the engine from YAML configuration
config_path = str((script_dir / 'config.yaml').resolve())

# Create engine from configuration file
# Environment variables will be automatically interpolated by Config.from_file
engine, config = engine_utils.create_from_config(config_path)

# Store the default model ID for later use
default_model = engine.default_model_id


@cl.on_chat_start
async def on_chat_start():
    await cl.Message(
        content=f"AI-6 is ready. Let's go 🚀!").send()


@cl.on_message
async def on_message(message: cl.Message):
    """Process user messages and generate responses."""
    # Create a new message for the response
    msg = cl.Message(content="")
    await msg.send()

    # Define a callback function to handle streaming chunks
    async def on_chunk(chunk: str):
        # Use the Chainlit built-in streaming method
        await msg.stream_token(chunk)

    # Stream the response
    try:
        response = engine.stream_message(
            message.content, 
            default_model, 
            on_chunk_func=lambda chunk: cl.run_sync(on_chunk(chunk))
        )
        # Mark the message as complete
        await msg.update()
    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()


if __name__ == "__main__":
    target = str(script_dir / "app.py")
    run_chainlit(target)
