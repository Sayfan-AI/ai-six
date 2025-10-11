"""Simple Slack posting tool"""
import os
import requests
from ai_six.object_model.tool import Tool, Parameter


class SlackPostTool(Tool):
    """Post messages to Slack channel using HTTP API"""

    def __init__(self):
        parameters = [
            Parameter(
                name='channel',
                type='string',
                description='Slack channel name (e.g., #makdo-devops)'
            ),
            Parameter(
                name='text',
                type='string',
                description='Message text to post'
            )
        ]

        super().__init__(
            name='slack_post_message',
            description='Post a message to a Slack channel',
            parameters=parameters,
            required={'channel', 'text'}
        )

        self.bot_token = os.getenv('AI6_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("AI6_BOT_TOKEN environment variable not set")

    def run(self, channel: str, text: str, **kwargs) -> str:
        """Post message to Slack channel"""

        # Ensure channel starts with #
        if not channel.startswith('#'):
            channel = f'#{channel}'

        url = 'https://slack.com/api/chat.postMessage'
        headers = {
            'Authorization': f'Bearer {self.bot_token}',
            'Content-Type': 'application/json'
        }
        data = {
            'channel': channel,
            'text': text
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()

            if result.get('ok'):
                return f"✅ Message posted to {channel}"
            else:
                error = result.get('error', 'unknown_error')
                return f"❌ Failed to post to {channel}: {error}"

        except Exception as e:
            return f"❌ Error posting to Slack: {str(e)}"
