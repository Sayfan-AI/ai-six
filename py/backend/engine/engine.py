import json
from typing import Callable

import sh
from openai import OpenAI

from ..tools.base.tool import Tool
from ..tools.base.tool_provider import ToolProvider


class Engine:
    def __init__(self, client: OpenAI, model_name: str):
        self.client = client
        self.model_name = model_name
        self.tools = []

    def register(self, tool_provider: Tool | ToolProvider):
        if isinstance(tool_provider, ToolProvider):
            self.tools += tool_provider.tools
        elif isinstance(tool_provider, Tool):
            self.tools.append(tool_provider)
        else:
            raise TypeError('tool_provider must be a Tool or a ToolProvider')

    def send(self,
             messages: list[dict[str, any]],
             tool_dict: dict[str, Tool],
             tool_list: list[dict[str, any]],
             tool_call_func: Callable[[str, dict, str], None] | None):
        try:
            response = self.client.chat.completions.create(
                model=self.model_name, messages=messages, tools=tool_list, tool_choice="auto")
            r = response.choices[0].message
        except Exception as e:
            raise
        if r.tool_calls:
            message = dict(
                role=r.role,
                content=r.content,
                tool_calls=[dict(
                    id=t.id,
                    type=t.type,
                    function=dict(
                        name=t.function.name,
                        arguments=t.function.arguments
                    )) for t in r.tool_calls if t.function])
            messages.append(message)
            for t in r.tool_calls:
                tool = tool_dict.get(t.function.name)
                if tool is None:
                    raise RuntimeError(f'Unknown tool: {t.function.name}')
                try:
                    kwargs = json.loads(t.function.arguments)
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Invalid arguments JSON for tool '{t.function.name}'")
                try:
                    result = tool.run(**kwargs)
                    tool_call =                         {
                            "tool_call_id": t.id,
                            "role": "tool",
                            "name": t.function.name,
                            "content": str(result),
                        }
                    messages.append(tool_call)
                    if tool_call_func is not None:
                        tool_call_func(tool_call['name'], kwargs, tool_call['content'])
                except sh.ErrorReturnCode as e:
                    messages.append(
                        {
                            "tool_call_id": t.id,
                            "role": "tool",
                            "name": t.function.name,
                            "content": e.stderr.decode(),
                        }
                    )
                except Exception as e:
                    messages.append(
                        {
                            "tool_call_id": t.id,
                            "role": "tool",
                            "name": t.function.name,
                            "content": str(e),
                        }
                    )

            return self.send(messages, tool_dict, tool_list, tool_call_func)
        return r.content.strip()

    def run(self,
            input_func: Callable[[str], None],
            tool_call_func: Callable[[str, dict, str], None] | None,
            output_func: Callable[[str], None]):
        """ """
        tool_dict = {t.spec.name: t for t in self.tools}
        tool_list = [t.as_dict() for t in self.tools]
        messages = []
        while user_input := input_func():
            messages.append(dict(role='user', content=user_input))

            response = self.send(messages, tool_dict, tool_list, tool_call_func)
            messages.append(dict(role='assistant',content=response))
            output_func(response)
        print('Done!')
