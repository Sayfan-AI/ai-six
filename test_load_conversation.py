import os
import json
from py.backend.memory.file_memory_provider import FileMemoryProvider
from py.backend.llm_providers.openai_provider import OpenAIProvider
from py.backend.engine.engine import Engine

# Set up the test environment
test_memory_dir = "test_data"
test_conversation_id = "test_conversation"

# Initialize providers
memory_provider = FileMemoryProvider(test_memory_dir)

# Check if the test conversation exists
print(f"Available conversations: {memory_provider.list_conversations()}")

# Load the conversation
messages = memory_provider.load_messages(test_conversation_id)
print(f"Loaded {len(messages)} messages")

# Print the messages
print("\nMessages:")
for i, msg in enumerate(messages):
    print(f"\nMessage {i+1}:")
    for key, value in msg.items():
        if key == "tool_calls" and value:
            print(f"  {key}: [")
            for tc in value:
                print(f"    {json.dumps(tc, indent=2)}")
            print("  ]")
        else:
            print(f"  {key}: {value}")

# Try to validate the messages
print("\nValidating messages...")
validated_messages = memory_provider._validate_message_structure(messages)
print(f"After validation: {len(validated_messages)} messages")

# Print the validated messages
print("\nValidated Messages:")
for i, msg in enumerate(validated_messages):
    print(f"\nValidated Message {i+1}:")
    for key, value in msg.items():
        if key == "tool_calls" and value:
            print(f"  {key}: [")
            for tc in value:
                print(f"    {json.dumps(tc, indent=2)}")
            print("  ]")
        else:
            print(f"  {key}: {value}")

# Try to create an OpenAI request with these messages
print("\nCreating OpenAI request...")
try:
    # We don't need a real API key for this test
    openai_provider = OpenAIProvider("dummy_key", "gpt-4o")
    
    # Create a minimal engine
    engine = Engine(
        llm_providers=[openai_provider],
        default_model_id="gpt-4o",
        tools_dir="py/backend/tools",
        memory_provider=memory_provider,
        conversation_id=test_conversation_id
    )
    
    # Load the conversation into the engine
    engine._load_conversation()
    print(f"Engine loaded {len(engine.messages)} messages")
    
    # Print the engine messages
    print("\nEngine Messages:")
    for i, msg in enumerate(engine.messages):
        print(f"\nEngine Message {i+1}:")
        for key, value in msg.items():
            if key == "tool_calls" and value:
                print(f"  {key}: [")
                for tc in value:
                    print(f"    {json.dumps(tc, indent=2)}")
                print("  ]")
            else:
                print(f"  {key}: {value}")
    
    print("\nTest completed successfully!")
except Exception as e:
    print(f"\nError: {e}")