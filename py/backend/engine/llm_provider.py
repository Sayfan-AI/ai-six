from abc import ABC, abstractmethod
from typing import Iterator, Callable, Dict, Any

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

    def stream(self, messages: list, tool_dict: dict[str, Tool], model: str | None = None) -> Iterator[Response]:
        """
        Stream a message to the LLM and receive responses as they are generated.
        :param messages: The list of messages to send.
        :param tool_dict: The tools available for the LLM to use.
        :param model: The model to use (optional).
        :return: An iterator of responses from the LLM.
        """
        # Default implementation just returns the full response
        yield self.send(messages, tool_dict, model)

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
