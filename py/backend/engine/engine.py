import json
import os.path
from pathlib import Path
from typing import Callable
import importlib.util
import inspect
import sh
from openai import OpenAI

from ..tools.base.tool import Tool
from ..tools.base.tool_provider import ToolProvider


class Engine:
    def __init__(self, client: OpenAI, model_name: str, tools_dir: str):
        assert (os.path.isdir(tools_dir))
        self.client = client
        self.model_name = model_name
        self.tools = Engine.discover_tools(tools_dir)

    @staticmethod
    def discover_tools(tools_dir):
        tools = []

        base_path = Path(tools_dir).resolve()  # e.g., /Users/gigi/git/ai-six/py/backend/tools
        module_root_path = base_path.parents[2]  # Three levels up → /Users/gigi/git/ai-six
        base_module = 'py.backend.tools'  # Static base module for tools

        # Walk through all .py files in the directory (recursive)
        for file_path in base_path.rglob("*.py"):
            if file_path.name == '__init__.py':
                continue

            try:
                # Get the path relative to the Python root dir
                relative_path = file_path.relative_to(module_root_path)

                # Convert path parts to a valid Python module name
                module_name = '.'.join(relative_path.with_suffix('').parts)

                # Validate it starts with the expected base_module
                if not module_name.startswith(base_module):
                    print(f"Skipping {module_name} (outside of {base_module})")
                    continue

                # Load module from file
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec is None:
                    print(f"Could not create spec for {module_name}")
                    continue

                module = importlib.util.module_from_spec(spec)

                try:
                    spec.loader.exec_module(module)
                except Exception as e:
                    print(f"Failed to import {module_name}: {e}")
                    continue

                # Inspect module for subclasses of Tool
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Tool) and obj is not Tool:
                        print(f"Found Tool subclass: {name} in {module_name}")
                        tool = obj()
                        tools.append(tool)

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        return tools

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
                    tool_call = {
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
            messages.append(dict(role='assistant', content=response))
            output_func(response)
        print('Done!')
