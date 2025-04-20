import json
import uuid

from py.backend.engine.object_model import (
    Usage
)
from py.backend.tools.base.tool import Tool, Spec, Parameters, Parameter


class Session:
    def __init__(self, memory_dir: str):
        self.session_id = str(uuid.uuid4())
        self.title = 'Untiled session ~' + self.session_id
        self.messages = []
        self.usage = Usage(0, 0)
        self.memory_dir = memory_dir

    def add_message(self, message: dict):
        self.messages.append(message)
        usage = message.get('usage', {})
        self.usage = Usage(
            self.usage.input_tokens + usage.get('input_tokens', 0),
            self.usage.output_tokens + usage.get('output_tokens', 0)
        )

    def save(self):
        d = dict(session_id=self.session_id,
                 title=self.title,
                 messages=self.messages,
                 usage=dict(
                    input_tokens=self.usage.input_tokens,
                    output_tokens=self.usage.output_tokens))
        filename = f"{self.memory_dir}/{self.session_id}.json"
        with open(filename, 'w') as f:
            json.dump(d, f, indent=4)

    def load(self, session_id: str):
        """Load session from disk, properly deserializing nested objects"""
        filename = f"{self.memory_dir}/{session_id}.json"
        with open(filename, 'r') as f:
            d = json.load(f)
        self.session_id = d['session_id']
        self.title = d['title']
        
        # Load messages as dictionaries
        self.messages = d['messages']
        
        # Deserialize usage directly to a Usage object
        self.usage = Usage(d['usage']['input_tokens'], d['usage']['output_tokens'])