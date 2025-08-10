from backend.engine.engine import Engine
from backend.engine.config import Config

class Agent:
    def __init__(self, config: Config, system_prompt: str):
        self.engine = Engine(config)

    def send_message(self, text: str, model: str | None = None) -> str:
        """
        Send a message to the LLM and return the response.

        :param text: The message text to send.
        :param model: The model to use (optional).
        :return: The response from the LLM.
        """
        if not text:
            raise ValueError("Message text cannot be empty.")

        response = self.engine.send(text, model=model)
        return response.text
