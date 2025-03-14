import os
import sys
from openai import OpenAI


# Get the absolute path to the project root (ai-six)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

from py.backend.engine.engine import Engine
from py.backend.tools.file_system.file_system import FileSystem

# Append it to sys.path
sys.path.append(ROOT_DIR)

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
    engine.run(get_user_input, print_to_console)

if __name__ == '__main__':
    main()