from py.backend.llm_providers.llm_provider import LLMProvider, Response, ToolCall
from py.backend.tools.base.tool import Tool
from openai import OpenAI


class OpenAIProvider(LLMProvider):

    def __init__(self, api_key: str, base_url: str, default_model: str = "gpt-4o"):
        super().__init__(api_key, base_url)
        self.default_model = default_model
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def send(self, messages: list, tool_list: list[Tool], model: str | None = None) -> Response:
        """
        Send a message to the OpenAI LLM and receive a response.
        :param messages: The list of messages to send.
        :param tool_list: The list of tools available for the LLM to use.
        :param model: The model to use (optional).
        :return: The response from the LLM.
        """
        if model is None:
            model = self.default_model

        # Send the message to the OpenAI API
        tool_data = [tool.as_dict() for tool in tool_list]
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tool_data,
            tool_choice="auto"
        )

        return response.choices[0].message.content

    def _build_tool_calls_message(self, response: Response) -> dict:
        """
        Build a message for the tool call.
        :param tool_call: The tool call to build the message for.
        :return: The message for the tool call.
        """
        return {
            "role": "assistant",
            "content": response.content,
            "tool_calls": [
                ToolCall(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=tool_call.function.arguments
                ) for tool_call in response.tool_calls if tool_call.function
            ]
        }




