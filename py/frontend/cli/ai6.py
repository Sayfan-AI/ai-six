import os

import pathology.path

from py.backend.llm_providers.openai_provider import OpenAIProvider
from ...backend.engine.engine import Engine

tools_dir = str((pathology.path.Path.script_dir() / '../../backend/tools').resolve())

def get_user_input():
    user_input = input("[You]: ")
    if user_input.lower() == 'exit':
        return None
    return user_input

def handle_response(response):
    print(f"[AI-6]: {response}")
    print('----------')

def handle_tool_call(name, args, result):
    print(f"[AI-6 tool call]: {name} {', '.join(args.values()) if args else ''}")
    print(result)
    print('----------')


def main():
    default_model = "gpt-4o"
    openai_provider = OpenAIProvider(
        os.environ['OPENAI_API_KEY'],
        default_model)

    engine = Engine([openai_provider], default_model, tools_dir)
    engine.run(get_user_input, handle_tool_call, handle_response)

if __name__ == '__main__':
    main()
