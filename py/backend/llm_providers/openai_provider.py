from py.backend.engine.llm_provider import LLMProvider, Response
from py.backend.engine.object_model import ToolCall, Usage

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
        :param tool_dict: The tools available for the LLM to use.
        :param messages: The list of messages to send.
        :param model: The model to use (optional).
        :return: The response from the LLM.
        """
        if model is None:
            model = self.default_model

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
        tool_calls = [] if tool_calls is None else tool_calls

        # Extract usage data
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

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
            usage=Usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
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
            ],
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens
        )
