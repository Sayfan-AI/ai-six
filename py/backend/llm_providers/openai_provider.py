from py.backend.llm_providers.llm_provider import LLMProvider, Response, ToolCall
from py.backend.tools.base.tool import Tool
from openai import OpenAI


class OpenAIProvider(LLMProvider):

    def __init__(self, api_key: str, default_model: str = "gpt-4o"):
        self.default_model = default_model
        self.client = OpenAI(api_key=api_key)

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

        return Response(
            content=response.choices[0].message.content,
            role=response.choices[0].message.role,
            tool_calls=[
                ToolCall(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=tool_call.function.arguments
                ) for tool_call in response.choices[0].message.tool_calls if tool_call.function
            ]
        )


    @property
    def models(self) -> list[str]:
        """ """
        return [m.id for m in self.client.models.list().data]

    def model_response_to_message(self, response: Response) -> dict:
        """
        Build a message with tool calls from a response.
        :return: The provider specific message
        """
        return {
            "role": "assistant",
            "content": response.content,
            "tool_calls": [
                ToolCall(
                    id=tool_call.id,
                    name=tool_call.name,
                    arguments=tool_call.arguments
                ) for tool_call in response.tool_calls if tool_call.function
            ]
        }

    def tool_result_to_message(self, tool_call: ToolCall, tool_result: str) -> dict:
        """
        Build a message from the result of a tool execution.
        :return: The provider specific message
        """
        return dict(
            tool_call_id = tool_call.id,
            role = "tool",
            name = tool_call.name,
            content = str(tool_result),
        )

