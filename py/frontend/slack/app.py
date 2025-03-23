import os
from functools import partial

import pathology.path
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from slack_sdk.errors import SlackApiError

from openai import OpenAI

from ...backend.engine.engine import Engine

tools_dir = str((pathology.path.Path.script_dir() / '../../backend/tools').resolve())

load_dotenv()

app_token = os.environ.get("AI6_APP_TOKEN")
bot_token = os.environ.get("AI6_BOT_TOKEN")

# Initializes your AI-6 app with your bot token and socket mode handler
app = App(token=bot_token)

last_message = ""

latest_ts = None

llm_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
model_name = "gpt-4o"

engine = Engine(llm_client, model_name, tools_dir)


@app.event("message")
def handle_message(message, ack, say):
    ack()  # Acknowledge ASAP

    text = message.get("text")
    if not text:
        return

    # Ignore messages with mention
    if "<@" in text:
        return

    channel_id = message['channel']

    # If you want to respond:
    # say(text=f"AI-6 is thinking... <@{user}>!", thread_ts=ts)

    response = engine.send_message(text, partial(handle_tool_call, channel_id=channel_id))

    post_to_channel(response, True, channel_id)


@app.event("channel_created")
def handle_channel_created(event, client, logger):
    """Automatically join any new channel whose name starts with 'ai-'"""
    channel = event['channel']
    if not channel['name'].startswith('ai-'):
        return

    channel_id = channel['id']
    logger.info(f"New channel created: {channel_id}")

    try:
        response = client.conversations_join(channel=channel_id)
        logger.info(f"Joined channel {channel_id}: {response}")
    except Exception as e:
        logger.error(f"Error joining channel {channel_id}: {e}")


def join_channel(client):
    """Join the first AI-6 channel if not a member already

    Return the channel id

    If there are no AI-6 channel raise an exception
    """
    channels = client.conversations_list()['channels']
    channels = [c for c in channels if c['name'].startswith('ai-6-')]
    if not channels:
        raise RuntimeError('No AI-6 channels!')

    channel = channels[0]
    channel_id = channel['id']

    # Join channel if not a member already
    if not channel['is_member']:
        try:
            client.conversations_join(channel=channel_id)
        except Exception as e:
            print(f"Error joining channel {channel_id}: {e}")

    return channel


def read_latest_message(channel_id):
    try:
        response = app.client.conversations_history(
            channel=channel_id,
            limit=1  # Only fetch the latest message
        )
        messages = response.get("messages", [])
        if messages:
            msg = messages[0]
            if 'bot_id' in msg:
                return None
            return msg
        else:
            print("No messages found.")
            return None

    except SlackApiError as e:
        print(f"Error fetching latest message: {e.response['error']}")
        return None


def post_to_channel(message: str, new_message: bool, channel_id: str):
    try:
        thread_ts = None if new_message else read_latest_message(channel_id).get('ts')
        app.client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=message
        )
    except SlackApiError as e:
        print(f"Error posting message: {e.response['error']}")


def handle_tool_call(name, args, result, channel_id):
    message = f"{name} {', '.join(args.values()) if args else ''}\n{result}\n{'-' * 10}"
    post_to_channel(message, False, channel_id)


def main():
    channel = join_channel(app.client)
    print(f'Joined {channel['name']}')

    # Start the Slack app
    SocketModeHandler(app, app_token).start()


if __name__ == "__main__":
    main()
