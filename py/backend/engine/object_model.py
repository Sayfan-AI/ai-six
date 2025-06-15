from typing import NamedTuple

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
