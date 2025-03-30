from abc import ABC, abstractmethod
from typing import NamedTuple

from py.backend.tools.base.tool import Tool


class ToolCall(NamedTuple):
    """
    A class to represent a tool call made by the LLM.
    """
    id: str
    name: str
    arguments: list


class Response(NamedTuple):
    """
    A class to represent a response from the LLM.
    """
    content: str
    role: str
    tool_calls: list[ToolCall]


class LLMProvider(ABC):
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

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
