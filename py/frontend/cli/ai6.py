import os

from openai import OpenAI

from ...backend.engine.engine import Engine
from ...backend.tools.file_system.file_system import FileSystem
from ...backend.tools.git.git import Git
from ...backend.tools.test_runner.test_runner import TestRunner

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

    engine = Engine(client, model_name)
    engine.register(FileSystem())
    engine.register(Git())
    engine.register(TestRunner())
    engine.run(get_user_input, handle_tool_call, handle_response)

if __name__ == '__main__':
    main()