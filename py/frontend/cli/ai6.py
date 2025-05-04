import os
import argparse
import pathology.path

from ..common import engine_utils

script_dir = pathology.path.Path.script_dir()

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
    parser.add_argument('--config', '-c', type=str, 
                        default=str((script_dir / 'config.json').resolve()),
                        help='Path to config file (default: config.json)')
    args = parser.parse_args()

    # Load configuration from JSON file
    config_path = args.config
    
    try:
        # Create engine from configuration, optionally loading a session
        engine, config = engine_utils.create_from_config(
            config_path, 
            session_id=args.session
        )
    except ValueError as e:
        return

    # Handle --list argument
    if args.list:
        sessions = engine.list_sessions()
        if sessions:
            for session_id in sessions:
                print(f"Session ID: {session_id}, Title: {sessions[session_id]['title']}")
        else:
            print("No sessions found.")
        return

    # Print current session ID

    # Run the session loop with streaming

    try:
        while user_input := get_user_input():
            print("[AI-6]:", end=' ', flush=True)
            response = engine.stream_message(
                user_input,
                engine.default_model_id,
                on_chunk_func=handle_chunk,
                on_tool_call_func=handle_tool_call
            )
            print("\n----------")
    finally:
        # Save the session when we're done
        print(f"Session saved with ID: {engine.get_session_id()}")

if __name__ == '__main__':
    main()