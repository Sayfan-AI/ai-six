from typing import Iterator
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

    def stream(self, messages: list, tool_dict: dict[str, Tool], model: str | None = None) -> Iterator[Response]:
        """
        Stream a message to the OpenAI LLM and receive responses as they are generated.
        :param messages: The list of messages to send.
        :param tool_dict: The tools available for the LLM to use.
        :param model: The model to use (optional).
        :return: An iterator of responses from the LLM.
        """
        if model is None:
            model = self.default_model

        tool_data = [self._tool2dict(tool) for tool in tool_dict.values()]

        try:
            # Create a streaming response with usage statistics
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tool_data if tool_data else None,
                tool_choice="auto" if tool_data else None,
                stream=True,
                stream_options={"include_usage": True}  # Get usage statistics in the final chunk
            )
        except Exception as e:
            raise

        # Initialize variables to accumulate the response
        content = ""
        role = "assistant"
        tool_calls = []
        current_tool_calls = {}
    
        # Track tokens for usage
        input_tokens = 0
        output_tokens = 0
    
        for chunk in stream:
            # Check if this is the final usage statistics chunk
            if chunk.usage:
                # Update usage statistics from the final chunk
                input_tokens = chunk.usage.prompt_tokens
                output_tokens = chunk.usage.completion_tokens
                continue
            
            # Skip chunks with no choices
            if not chunk.choices:
                continue
            
            # Update content if available
            if chunk.choices[0].delta.content:
                content += chunk.choices[0].delta.content
            
                # Yield a partial response with the updated content
                yield Response(
                    content=content,
                    role=role,
                    tool_calls=[],  # No tool calls yet
                    usage=None  # We'll only have accurate usage at the end
                )
        
            # Handle tool calls
            if chunk.choices[0].delta.tool_calls:
                for delta_tool_call in chunk.choices[0].delta.tool_calls:
                    # Initialize tool call if it's new
                    if delta_tool_call.index not in current_tool_calls:
                        current_tool_calls[delta_tool_call.index] = {
                            "id": delta_tool_call.id or "",
                            "function": {
                                "name": "",
                                "arguments": ""
                            }
                        }
                
                    # Update tool call ID if provided
                    if delta_tool_call.id:
                        current_tool_calls[delta_tool_call.index]["id"] = delta_tool_call.id
                
                    # Update function name if provided
                    if delta_tool_call.function and delta_tool_call.function.name:
                        current_tool_calls[delta_tool_call.index]["function"]["name"] = delta_tool_call.function.name
                
                    # Update function arguments if provided
                    if delta_tool_call.function and delta_tool_call.function.arguments:
                        current_tool_calls[delta_tool_call.index]["function"]["arguments"] += delta_tool_call.function.arguments
        
            # If we have a finish reason, check if it's for tool calls
            if chunk.choices[0].finish_reason == "tool_calls":
                # Convert accumulated tool calls to ToolCall objects
                tool_calls = []
                for tool_call_data in current_tool_calls.values():
                    function_name = tool_call_data["function"]["name"]
                    if function_name in tool_dict:
                        tool_calls.append(
                            ToolCall(
                                id=tool_call_data["id"],
                                name=function_name,
                                arguments=tool_call_data["function"]["arguments"],
                                required=tool_dict[function_name].spec.parameters.required
                            )
                        )
            
                # Yield a response with the tool calls
                yield Response(
                    content=content,
                    role=role,
                    tool_calls=tool_calls,
                    usage=None  # We'll only have accurate usage at the end
                )
    
        # Yield the final complete response with usage statistics
        if not tool_calls:
            # Convert accumulated tool calls to ToolCall objects if we haven't already
            tool_calls = []
            for tool_call_data in current_tool_calls.values():
                function_name = tool_call_data["function"]["name"]
                if function_name in tool_dict:
                    tool_calls.append(
                        ToolCall(
                            id=tool_call_data["id"],
                            name=function_name,
                            arguments=tool_call_data["function"]["arguments"],
                            required=tool_dict[function_name].spec.parameters.required
                        )
                    )
    
        # Yield the final complete response with usage statistics
        yield Response(
            content=content,
            role=role,
            tool_calls=tool_calls,
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
