import os

import pathology.path
from openai import OpenAI

from ...backend.engine.engine_orig import Engine

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
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    model_name = "gpt-4o"

    engine = Engine(client, model_name, tools_dir)
    engine.run(get_user_input, handle_tool_call, handle_response)

if __name__ == '__main__':
    main()
