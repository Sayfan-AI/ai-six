from py.backend.llm_providers.llm_provider import LLMProvider, Response, ToolCall
from py.backend.tools.base.tool import Tool
from openai import OpenAI


class OpenAIProvider(LLMProvider):

    def __init__(self, api_key: str, default_model: str = "gpt-4o"):
        self.default_model = default_model
        self.client = OpenAI(api_key=api_key)

    @staticmethod
    def _tool2dict(tool: Tool) -> dict:
        """Convert the tool to a dictionary format for OpenAI API."""
        return {
            "type": "function",
            "function": {
                "name": tool.spec.name,
                "description": tool.spec.description,
                "parameters": {
                    "type": "object",
                    "required": tool.spec.parameters.required,
                    "properties": {
                        param.name: {
                            "type": param.type,
                            "description": param.description
                        } for param in tool.spec.parameters.properties
                    },
                }
            }
        }

    def send(self, messages: list, tool_dict: dict[str, Tool], model: str | None = None) -> Response:
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
        tool_data = [self._tool2dict(tool) for tool in tool_dict.values()]

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tool_data,
                tool_choice="auto"
            )
        except Exception as e:
            raise

        tool_calls = response.choices[0].message.tool_calls
        tool_calls = [] if tool_calls is None else tool_calls# Check if the response contains tool calls
        return Response(
            content=response.choices[0].message.content,
            role=response.choices[0].message.role,
            tool_calls=[
                ToolCall(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=tool_call.function.arguments,
                    required=tool_dict[tool_call.function.name].spec.parameters.required
                ) for tool_call in tool_calls if tool_call.function
            ],
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
        # return {
        #     "role": "assistant",
        #     "content": response.content,
        #     "tool_calls": [
        #         ToolCall(
        #             id=tool_call.id,
        #             name=tool_call.name,
        #             arguments=tool_call.arguments
        #         ) for tool_call in response.tool_calls
        #     ]
        # }

        return dict(role="assistant",
            content=response.content,
            tool_calls=[
                dict(
                    id=t.id,
                    type="function",
                    function=dict(
                        name=t.name,
                        arguments=t.arguments
                    )
                ) for t in response.tool_calls
            ]
        )


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
