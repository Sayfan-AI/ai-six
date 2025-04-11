import json
import os
from pathlib import Path

def validate_and_fix_conversation(conversation_path):
    """
    Validate and fix a conversation file to ensure all tool messages have corresponding tool_calls.
    
    Args:
        conversation_path: Path to the conversation JSON file
    """
    print(f"Processing {conversation_path}...")
    
    # Load the conversation
    with open(conversation_path, 'r') as f:
        messages = json.load(f)
    
    print(f"Loaded {len(messages)} messages")
    
    # Validate and fix the messages
    validated_messages = validate_message_structure(messages)
    
    print(f"After validation: {len(validated_messages)} messages")
    
    # Save the fixed conversation
    with open(conversation_path, 'w') as f:
        json.dump(validated_messages, f, indent=2)
    
    print(f"Saved fixed conversation to {conversation_path}")

def validate_message_structure(messages):
    """
    Validate and fix the message structure to ensure compatibility with OpenAI API.
    
    This ensures that:
    1. Messages with role 'tool' have a corresponding preceding message with 'tool_calls'
    2. Messages have the correct structure for the API
    3. No duplicate messages exist
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        List of validated and fixed messages
    """
    validated_messages = []
    tool_call_ids_seen = set()
    message_hashes = set()  # To detect duplicates
    
    for i, message in enumerate(messages):
        # Skip messages with invalid roles
        if 'role' not in message:
            print(f"Skipping message {i} - missing role")
            continue
        
        # Create a hash of the message to detect duplicates
        # We'll use a tuple of (role, content, tool_call_id) as the hash
        msg_hash = (
            message.get('role'),
            message.get('content'),
            message.get('tool_call_id') if message.get('role') == 'tool' else None
        )
        
        # Skip duplicate messages
        if msg_hash in message_hashes:
            print(f"Skipping duplicate message {i} - role: {message.get('role')}")
            continue
        
        message_hashes.add(msg_hash)
        
        # Handle tool messages
        if message.get('role') == 'tool':
            # Check if this tool message has a valid tool_call_id
            if 'tool_call_id' not in message:
                print(f"Skipping tool message {i} - missing tool_call_id")
                continue
                
            # Check if we've seen a corresponding tool_call
            if message['tool_call_id'] not in tool_call_ids_seen:
                print(f"Skipping tool message {i} - no corresponding tool_call found for ID: {message['tool_call_id']}")
                continue
                
            # Add the valid tool message
            validated_messages.append(message)
        else:
            # For non-tool messages, check if it has tool_calls
            if 'tool_calls' in message and message.get('role') == 'assistant':
                # Add all tool_call_ids to our seen set
                for tool_call in message['tool_calls']:
                    if 'id' in tool_call:
                        tool_call_ids_seen.add(tool_call['id'])
                        print(f"Found tool_call ID: {tool_call['id']}")
            
            # Add the message
            validated_messages.append(message)
    
    return validated_messages

def main():
    # Process test conversation
    test_path = Path("/workspace/ai-six/test_data/conversations/test_conversation.json")
    if test_path.exists():
        validate_and_fix_conversation(test_path)
    
    # Process all conversations in the memory directory
    memory_dir = Path("/workspace/ai-six/memory")
    if memory_dir.exists():
        for conversations_dir in memory_dir.glob("*/conversations"):
            for conv_file in conversations_dir.glob("*.json"):
                validate_and_fix_conversation(conv_file)

if __name__ == "__main__":
    main()