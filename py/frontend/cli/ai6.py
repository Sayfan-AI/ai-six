import os
import argparse
import pathology.path
from pathlib import Path

from py.backend.llm_providers.openai_provider import OpenAIProvider
from ...backend.engine.engine import Engine

# Get the tools directory
tools_dir = str((pathology.path.Path.script_dir() / '../../backend/tools').resolve())

# Get the memory directory (create it if it doesn't exist)
memory_dir = str((pathology.path.Path.script_dir() / '../../../memory/cli').resolve())
Path(memory_dir).mkdir(parents=True, exist_ok=True)

def get_user_input():
    user_input = input("[You]: ")
    if user_input.lower() == 'exit':
        return None
    return user_input

def handle_response(response):
    print(f"\n[AI-6]: {response}")
    print('----------')

def handle_chunk(chunk):
    print(chunk, end='', flush=True)

def handle_tool_call(name, args, result):
    print(f"\n[AI-6 tool call]: {name} {', '.join(args.values()) if args else ''}")
    print(result)
    print('----------')

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='AI-6 CLI with session support')
    parser.add_argument('--session', '-s', type=str, help='Session ID to load')
    parser.add_argument('--list', '-l', action='store_true', help='List available sessions')
    args = parser.parse_args()

    # Initialize OpenAI provider
    default_model = "gpt-4o"
    openai_provider = OpenAIProvider(
        os.environ['OPENAI_API_KEY'],
        default_model)

    # Initialize engine with session support
    engine = Engine(
        llm_providers=[openai_provider],
        default_model_id=default_model,
        tools_dir=tools_dir,
        memory_dir=memory_dir,
        session_id=args.session
    )

    # Handle --list argument
    if args.list:
        sessions = engine.list_sessions()
        if sessions:
            print("Available sessions:")
            for session_id in sessions:
                print(f"- {session_id}")
        else:
            print("No sessions found.")
        return

    # Print current session ID
    print(f"Current session ID: {engine.get_session_id()}")

    # Run the session loop with streaming
    print("AI-6 CLI with streaming support. Type 'exit' to quit.")

    try:
        while user_input := get_user_input():
            print("[AI-6]:", end=' ', flush=True)
            response = engine.stream_message(
                user_input,
                default_model,
                on_chunk_func=handle_chunk,
                on_tool_call_func=handle_tool_call
            )
            print("\n----------")
    finally:
        # Save the session when we're done
        print(f"Session saved with ID: {engine.get_session_id()}")

if __name__ == '__main__':
    main()