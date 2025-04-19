import json
from py.backend.llm_providers.llm_provider import LLMProvider, Response, ToolCall
from py.backend.tools.base.tool import Tool

import ollama


class OllamaProvider(LLMProvider):
    def __init__(self, model: str):
        self.model = model

    @property
    def models(self) -> list[str]:
        """Get the list of available models."""
        # This should return actual available models for ollama
        return [self.model]  # Example: return the initialized model


    @staticmethod
    def _fix_tool_call_arguments(messages):
        for message in messages:
            tool_calls = message.get("tool_calls")
            if not tool_calls:
                continue
            for call in tool_calls:
                func = call.get("function")
                if func and isinstance(func.get("arguments"), str):
                    try:
                        func["arguments"] = json.loads(func["arguments"])
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON in function.arguments: {func['arguments']}") from e


    def send(self, messages: list, tool_dict: dict[str, Tool], model: str | None = None) -> Response:
        """Send a message to the local Ollama model and receive a response."""
        if model is None:
            model = self.model

        # Convert tools to the format required by ollama's chat function
        tool_data = [tool.run for tool in tool_dict.values()] + [self._tool2dict(tool) for tool in tool_dict.values()]

        try:
            OllamaProvider._fix_tool_call_arguments(messages)
            response: ollama.ChatResponse = ollama.chat(
                model,
                messages=messages,
                tools=tool_data
            )
        except Exception as e:
            raise RuntimeError(f"Error communicating with ollama model: {e}")

        tool_calls = response.message.tool_calls or []
        return Response(
            content=response.message.content,
            role=response.message.role,
            tool_calls=[
                ToolCall(
                    id=tool_call.function.name,
                    name=tool_call.function.name,
                    arguments=json.dumps(tool_call.function.arguments),
                    required=tool_dict[tool_call.function.name].spec.parameters.required
                ) for tool_call in tool_calls if tool_call
            ],
        )

    def model_response_to_message(self, response: Response) -> dict:
        """Convert the response to a message format."""
        return dict(
            role="assistant",
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



    @staticmethod
    def _tool2dict(tool: Tool) -> dict:
        """Convert the tool to a dictionary format for Ollama."""
        return {
            'type': 'function',
            'function': {
                'name': tool.spec.name,
                'description': tool.spec.description,
                'parameters': {
                    'type': 'object',
                    'required': tool.spec.parameters.required,
                    'properties': {
                        param.name: {
                            'type': param.type,
                            'description': param.description
                        } for param in tool.spec.parameters.properties
                    },
                }
            }
        }
