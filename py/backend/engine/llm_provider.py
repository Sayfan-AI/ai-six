from abc import ABC, abstractmethod

from py.backend.engine.object_model import Response
from py.backend.tools.base.tool import Tool


class LLMProvider(ABC):
    @abstractmethod
    def send(self, messages: list, tool_list: list[Tool], model: str | None = None) -> Response:
        """
        Send a message to the LLM and receive a response.
        :param messages: The list of messages to send.
        :param tool_list: The list of tools available for the LLM to use.
        :param model: The model to use (optional).
        :return: The response from the LLM.
        """
        pass

    @property
    @abstractmethod
    def models(self) -> list[str]:
        """ Get the list of available models."""
        pass

    @abstractmethod
    def model_response_to_message(self, response: Response) -> dict:
        """
        Convert the response to a message format.
        :param response: The response from the LLM.
        :return: The message in a dictionary format.
        """
        pass
