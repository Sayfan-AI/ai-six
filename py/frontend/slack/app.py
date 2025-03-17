import os
import time

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from openai import OpenAI

from ...backend.engine.engine import Engine
from ...backend.tools.file_system.file_system import FileSystem
from ...backend.tools.git.git import Git
from ...backend.tools.test_runner.test_runner import TestRunner

# Load environment variables from a .env file
load_dotenv()

app_token = os.environ.get("AI6_APP_TOKEN")
bot_token = os.environ.get("AI6_BOT_TOKEN")
# Initializes your AI-6 app with your bot token and socket mode handler
app = App(token=bot_token)


last_message = ""

@app.message()
def handle_message(message, say):

    say(
        text=f"Hey there <@{message['user']}>!")

@app.action("button_click")
def action_button_click(body, ack, say):
    # Acknowledge the action
    ack()
    say(f"<@{body['user']['id']}> clicked the button", thread_ts=body['message']['ts'])

@app.event("channel_created")
def handle_channel_created(event, client, logger):
    """Automatically join any new channel whose name starts with 'ai-'"""
    channel = event['channel']
    if not channel['name'].startswith('ai-'):
        return

    channel_id = channel['id']
    logger.info(f"New channel created: {channel_id}")

    try:
        # Bot joins the newly created public channel
        response = client.conversations_join(channel=channel_id)
        logger.info(f"Joined channel {channel_id}: {response}")
    except Exception as e:
        logger.error(f"Error joining channel {channel_id}: {e}")


def join_channels(client):
    channels = client.conversations_list()['channels']
    channels = [c for c in channels if c['name'].startswith('ai-6-') and not c['is_member']]
    for c in channels:
        channel_id = c['id']
        try:
            client.conversations_join(channel=channel_id)
        except Exception as e:
            raise


def get_user_message():
    global last_message
    while not last_message:
        time.sleep(0.1)

    result = last_message
    last_message = ""
    return result

def post_to_channel(channel_id, message):
        try:
            response = app.client.chat_postMessage(
                channel=channel_id,
                text=text
            )
            print(f"Message sent to {channel_id}: {response['ts']}")
        except SlackApiError as e:
            print(f"Error posting message: {e.response['error']}")


def start_ai6_engine(input_func, output_func):
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    model_name = "gpt-4o"

    engine = Engine(client, model_name)
    engine.register(FileSystem())
    engine.register(Git())
    engine.register(TestRunner())
    engine.run(input_func, output_func)

if __name__ == "__main__":
    join_channels(app.client)
    SocketModeHandler(app, app_token).start()




