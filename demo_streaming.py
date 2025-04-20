import os
import sys
from py.backend.llm_providers.openai_provider import OpenAIProvider
from py.backend.engine.engine import Engine
from pathlib import Path

def main():
    """Demonstrate streaming functionality with the OpenAI provider."""
    # Check if API key is provided
    if len(sys.argv) < 2:
        print("Usage: python demo_streaming.py YOUR_OPENAI_API_KEY")
        return
    
    api_key = sys.argv[1]
    
    # Set up directories
    tools_dir = "py/backend/tools"
    memory_dir = "memory/demo"
    Path(memory_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize the provider and engine
    default_model = "gpt-4o"
    provider = OpenAIProvider(api_key, default_model)
    
    engine = Engine(
        llm_providers=[provider],
        default_model_id=default_model,
        tools_dir=tools_dir,
        memory_dir=memory_dir
    )
    
    # Define callback functions
    def handle_chunk(chunk):
        print(chunk, end='', flush=True)
    
    def handle_tool_call(name, args, result):
        print(f"\n[Tool Call]: {name}")
        print(f"Arguments: {args}")
        print(f"Result: {result}")
    
    # Run a simple conversation with streaming
    print("AI-6 Streaming Demo")
    print("-------------------")
    print("Type 'exit' to quit")
    
    try:
        while True:
            # Get user input
            user_input = input("\nYou: ")
            if user_input.lower() == 'exit':
                break
            
            # Stream the response
            print("\nAI: ", end='', flush=True)
            response = engine.stream_message(
                user_input,
                default_model,
                on_chunk_func=handle_chunk,
                on_tool_call_func=handle_tool_call
            )
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        print(f"\nSession saved with ID: {engine.get_session_id()}")

if __name__ == "__main__":
    main()