import os
import sys
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

def print_to_console(response):
    print(f"[AI-6]: {response}")
    print('----------')


def main():
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    model_name = "gpt-4o"

    engine = Engine(client, model_name)
    engine.register(FileSystem())
    engine.register(Git())
    engine.register(TestRunner())
    engine.run(get_user_input, print_to_console)

if __name__ == '__main__':
    main()