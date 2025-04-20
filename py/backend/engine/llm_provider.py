from abc import ABC, abstractmethod, abstractproperty
from typing import NamedTuple

from py.backend.tools.base.tool import Tool


class ToolCall(NamedTuple):
    """
    A class to represent a tool call made by the LLM.
    """
    id: str
    name: str
    arguments: list
    required: list[str]


class Usage(NamedTuple):
    """
    A class to represent the usage information.
    """
    input_tokens: int
    output_tokens: int


class Response(NamedTuple):
    """
    A class to represent a response from the LLM.
    """
    content: str
    role: str
    tool_calls: list[ToolCall]
    usage: Usage


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

