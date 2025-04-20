import os
from functools import partial
from pathlib import Path

import pathology.path
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from slack_sdk.errors import SlackApiError

from openai import OpenAI

from py.backend.llm_providers.openai_provider import OpenAIProvider
from ...backend.engine.engine import Engine

# Get the tools directory
tools_dir = str((pathology.path.Path.script_dir() / '../../backend/tools').resolve())

# Get the memory directory (create it if it doesn't exist)
memory_dir = str((pathology.path.Path.script_dir() / '../../../memory/slack').resolve())
Path(memory_dir).mkdir(parents=True, exist_ok=True)

load_dotenv()

app_token = os.environ.get("AI6_APP_TOKEN")
bot_token = os.environ.get("AI6_BOT_TOKEN")

# Initializes your AI-6 app with your bot token and socket mode handler
app = App(token=bot_token)

last_message = ""
latest_ts = None

# Initialize providers
default_model = "gpt-4o"
openai_provider = OpenAIProvider(
    os.environ['OPENAI_API_KEY'],
    default_model)

# Initialize engines with separate session storage per channel
engines = {}

def get_or_create_engine(channel_id):
    """Get an existing engine for a channel or create a new one."""
    if channel_id not in engines:
        # Create a channel-specific memory directory
        channel_memory_dir = f"{memory_dir}/{channel_id}"
        Path(channel_memory_dir).mkdir(exist_ok=True)
        
        # Create a new engine for this channel
        engines[channel_id] = Engine(
            llm_providers=[openai_provider],
            default_model_id=default_model,
            tools_dir=tools_dir,
            memory_dir=channel_memory_dir
        )
    
    return engines[channel_id]

def handle_tool_call(client, channel, name, args, result):
    """Handle a tool call from the AI-6 engine."""
    # Post the tool call result as a message
    try:
        client.chat_postMessage(
            channel=channel,
            text=f"_Tool call: `{name}` {', '.join(args.values()) if args else ''}_\n{result}"
        )
    except SlackApiError as e:
        print(f"Error posting tool call result: {e}")

@app.event("app_mention")
def handle_app_mention(event, say, client):
    """Handle when the app is mentioned in a channel."""
    global last_message, latest_ts

    # Extract the text without the mention
    text = event["text"]
    text = text.replace(f"<@{event['user']}>", "").strip()
    print(f"Received message: {text}")
    
    # Skip if the message is empty or just contains the mention
    if not text:
        say("How can I help you today?")
        return
    
    # Get or create an engine for this channel
    channel_id = event["channel"]
    engine = get_or_create_engine(channel_id)
    
    # Create a tool call handler for this channel
    channel_tool_call_handler = partial(handle_tool_call, client, channel_id)
    
    # Process the message with the AI-6 engine
    try:
        # Send a typing indicator
        client.chat_postEphemeral(
            channel=channel_id,
            user=event["user"],
            text="AI-6 is thinking..."
        )
        
        # Post an initial empty message that we'll update
        result = client.chat_postMessage(
            channel=channel_id,
            text="..."
        )
        
        latest_ts = result["ts"]
        last_message = ""
        
        # Define a callback function to handle streaming chunks
        def handle_chunk(chunk):
            nonlocal last_message
            last_message += chunk
            
            try:
                # Update the message with the new content
                client.chat_update(
                    channel=channel_id,
                    ts=latest_ts,
                    text=last_message
                )
            except SlackApiError as e:
                print(f"Error updating message: {e}")
        
        # Stream the message to the AI-6 engine
        response = engine.stream_message(
            text, 
            default_model, 
            on_chunk_func=handle_chunk,
            on_tool_call_func=channel_tool_call_handler
        )
        
    except Exception as e:
        say(f"I encountered an error: {str(e)}")

if __name__ == "__main__":
    handler = SocketModeHandler(app, app_token)
    handler.start()