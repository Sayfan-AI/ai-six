import json
import os.path
from pathlib import Path
from typing import Callable
import importlib.util
import inspect
import sh

from ..llm_providers.llm_provider import LLMProvider
from ..tools.base.tool import Tool

class Engine:
    def __init__(self, llm_providers: list[LLMProvider], default_model_id: str, tools_dir: str):
        assert (os.path.isdir(tools_dir))
        self.llm_providers = llm_providers
        self.default_model_id = default_model_id
        self.model_provider_map = {
            model_id: llm_provider
            for llm_provider in llm_providers
            for model_id in llm_provider.models
        }
        tools = Engine.discover_tools(tools_dir)
        self.tool_dict = {t.spec.name: t for t in tools}
        self.tool_list = [t.as_dict() for t in tools]
        self.messages = []

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

    def _send(self, model_id, on_tool_call_func: Callable[[str, dict, str], None] | None) -> str:
        llm_provider = self.model_provider_map.get(model_id)
        if llm_provider is None:
            raise RuntimeError(f"Unknown model ID: {model_id}")

        response = llm_provider.send(self.messages, self.tool_list, model_id)
        if response.tool_calls:
            message = llm_provider.model_response_to_message(response)
            self.messages.append(message)
            for tool_call in response.tool_calls:
                tool = self.tool_dict.get(tool_call.name)
                if tool is None:
                    raise RuntimeError(f'Unknown tool: {tool_call.name}')
                try:
                    kwargs = json.loads(tool_call.arguments)
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Invalid arguments JSON for tool '{tool_call.name}'")
                try:
                    tool_result = tool.run(**kwargs)
                    message = llm_provider.tool_result_to_message(tool_call, str(tool_result))
                    if on_tool_call_func is not None:
                        on_tool_call_func(message['name'], kwargs, message['content'])
                except sh.ErrorReturnCode as e:
                    message = llm_provider.tool_result_to_message(tool_call, e.stderr.decode())
                except Exception as e:
                    message = llm_provider.tool_result_to_message(tool_call, str(e))
                finally:
                    self.messages.append(message)

            return self._send(model_id, on_tool_call_func)
        return response.content.strip()

    def run(self,
            get_input_func: Callable[[], None],
            on_tool_call_func: Callable[[str, dict, str], None] | None,
            on_response_func: Callable[[str], None]):
        """ """
        while user_input := get_input_func():
            self.messages.append(dict(role='user', content=user_input))

            response = self._send(self.default_model_id, on_tool_call_func)
            self.messages.append(dict(role='assistant', content=response))
            on_response_func(response)
        print('Done!')

    def send_message(self, message: str, model_id: str, on_tool_call_func: Callable[[str, dict, str], None] | None) -> str:
        self.messages.append(dict(role='user', content=message))
        response = self._send(model_id, on_tool_call_func)
        return response
