import os
import re
from functools import partial

from multiprocessing import Process, Queue
from time import sleep

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from slack_sdk.errors import SlackApiError

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

message_queue = Queue()


# @app.event("message")
# def handle_message(message, ack, say):
#     ack()  # Acknowledge ASAP
#
#     text = message.get("text")
#     if not text:
#         return
#
#     print(f"New user message: {text}")
#
#     message_queue.put(text)
#
#     # If you want to respond:
#     # say(text=f"AI-6 is thinking... <@{user}>!", thread_ts=ts)


# @app.action("button_click")
# def action_button_click(body, ack, say):
#     ack()
#     say(f"<@{body['user']['id']}> clicked the button", thread_ts=body['message']['ts'])

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


def get_user_message(message_queue: Queue):
    new_message = message_queue.get()  # blocks until message is available
    return new_message

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


def post_to_channel(message, channel_id):
    try:
        response = app.client.chat_postMessage(
            channel=channel_id,
            text=message  # Fixed variable name
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


def main():
    channel = join_channel(app.client)
    print(f'Joined {channel['name']}')

    # Start the AI 6 engine
    engine_process = Process(
        target=start_ai6_engine,
        args=(partial(get_user_message, message_queue),
              partial(post_to_channel, channel_id=channel['id'])))
    engine_process.start()

    # Start the Slack app
    # SocketModeHandler(app, app_token).start()

    try:
        latest_ts = None
        while True:
            try:
                message = read_latest_message(channel['id'])

                if message is not None and (latest_ts is None or message['ts'] > latest_ts):
                    latest_ts = message['ts']
                    message_queue.put(message['text'])
                else:
                    sleep(1)
            except KeyboardInterrupt:
                print("\nCtrl+C detected. Exiting loop...")
                break

    finally:
        print("Shutting down AI-6 engine...")
        engine_process.terminate()
        engine_process.join()
        print("Shutdown complete.")


if __name__ == "__main__":
    main()
