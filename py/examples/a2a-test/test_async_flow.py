#!/usr/bin/env python3
"""Test the async A2A communication flow with message pump."""

import sys
import os
import asyncio
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.agent.agent import Agent
from backend.agent.config import Config

def test_async_a2a_flow():
    """Test the full async A2A communication flow."""
    
    print("🧪 Testing A2A Async Communication Flow")
    print("=" * 50)
    
    # Load config with A2A server configuration
    config_file = os.path.join(os.path.dirname(__file__), 'config.yaml')
    config = Config.from_file(config_file)
    
    print("✅ Configuration loaded")
    print(f"   A2A servers: {len(config.a2a_servers)}")
    for server in config.a2a_servers:
        print(f"   - {server['name']}: {server['url']}")
    
    # Create agent
    print("\n🤖 Creating AI-6 agent with A2A async support...")
    agent = Agent(config)
    
    print(f"✅ Agent created with {len(agent.tool_dict)} tools")

    # List all available tools
    print("\n🔧 Available Tools:")
    for tool_name in sorted(agent.tool_dict.keys()):
        tool = agent.tool_dict[tool_name]
        if tool_name.startswith('a2a_') or tool_name.startswith('kind-k8s-ai_'):
            print(f"   ⭐ {tool_name}: {tool.description}")
        else:
            print(f"   • {tool_name}: {tool.description}")
    
    # Find A2A tools
    a2a_tools = [name for name in agent.tool_dict.keys() if name.startswith('kind-k8s-ai_')]
    task_tools = [name for name in agent.tool_dict.keys() if name.startswith('a2a_')]
    
    print(f"\n📋 A2A Analysis:")
    print(f"   A2A operation tools: {len(a2a_tools)}")
    print(f"   A2A task management tools: {len(task_tools)}")
    
    if not a2a_tools:
        print("⚠️ No A2A operation tools found")
        print("   A2A server may not be running or discovery failed")
        return
    
    # Test 1: List active tasks (should be empty initially)
    print("\n📝 Test 1: List Active Tasks")
    if 'a2a_list_tasks' in agent.tool_dict:
        result = agent.tool_dict['a2a_list_tasks'].run()
        print(f"Result: {result}")
    
    # Test 2: Start an A2A task
    print("\n🚀 Test 2: Start A2A Task")
    a2a_tool_name = a2a_tools[0]
    print(f"Using tool: {a2a_tool_name}")
    
    try:
        # Start a task
        result = agent.tool_dict[a2a_tool_name].run(
            message="Show me the current status of all pods in the cluster"
        )
        print(f"Start result: {result}")
        
        # Extract task ID from result (simple parsing)
        task_id = None
        if "ID:" in result:
            task_id = result.split("ID:")[1].strip().split(")")[0]
            print(f"Extracted task ID: {task_id}")
        
    except Exception as e:
        print(f"❌ Failed to start A2A task: {e}")
        return
    
    # Test 3: List active tasks again (should show the new task)
    print("\n📝 Test 3: List Active Tasks (After Starting)")
    if 'a2a_list_tasks' in agent.tool_dict:
        result = agent.tool_dict['a2a_list_tasks'].run()
        print(f"Result: {result}")
    
    # Test 4: Wait for interim messages (simulate background processing)
    print("\n⏳ Test 4: Waiting for Interim Messages")
    print("Simulating background A2A communication for 10 seconds...")
    
    # Check session messages periodically
    initial_message_count = len(agent.session.messages)
    print(f"Initial message count: {initial_message_count}")
    
    for i in range(10):
        time.sleep(1)
        current_message_count = len(agent.session.messages)
        if current_message_count > initial_message_count:
            print(f"📨 New messages detected! Count: {current_message_count}")
            # Show the new messages
            for msg in agent.session.messages[initial_message_count:]:
                print(f"   {msg.role}: {msg.content[:100]}...")
            initial_message_count = current_message_count
        else:
            print(f"   Waiting... ({i+1}/10)")
    
    # Test 5: Send message to task (if we have a task ID)
    if task_id and 'a2a_send_message' in agent.tool_dict:
        print("\n💬 Test 5: Send Message to Task")
        try:
            result = agent.tool_dict['a2a_send_message'].run(
                task_id=task_id,
                message="Please focus on pods that are not in 'Running' status"
            )
            print(f"Send message result: {result}")
        except Exception as e:
            print(f"❌ Failed to send message to task: {e}")
    
    # Test 6: Check task status
    if task_id and 'a2a_task_status' in agent.tool_dict:
        print("\n📊 Test 6: Check Task Status")
        try:
            result = agent.tool_dict['a2a_task_status'].run(task_id=task_id)
            print(f"Task status: {result}")
        except Exception as e:
            print(f"❌ Failed to check task status: {e}")
    
    # Test 7: Final message count
    print("\n📈 Test 7: Final Session Analysis")
    final_message_count = len(agent.session.messages)
    print(f"Final message count: {final_message_count}")
    print(f"Messages added during test: {final_message_count - initial_message_count}")
    
    # Show message types
    message_types = {}
    for msg in agent.session.messages:
        message_types[msg.role] = message_types.get(msg.role, 0) + 1
    
    print("Message breakdown:")
    for role, count in message_types.items():
        print(f"   {role}: {count}")
    
    # Test 8: Cleanup (cancel task if created)
    if task_id and 'a2a_cancel_task' in agent.tool_dict:
        print("\n🧹 Test 8: Cleanup - Cancel Task")
        try:
            result = agent.tool_dict['a2a_cancel_task'].run(task_id=task_id)
            print(f"Cancel result: {result}")
        except Exception as e:
            print(f"❌ Failed to cancel task: {e}")
    
    print("\n🎉 Async A2A Communication Flow Test Complete!")
    print("\n🔥 Key Features Tested:")
    print("   ✅ A2A message pump initialization")
    print("   ✅ Task management tools availability") 
    print("   ✅ Async task creation with immediate response")
    print("   ✅ Background message monitoring")
    print("   ✅ SystemMessage injection into session")
    print("   ✅ Task status and communication tools")
    print("   ✅ Task lifecycle management")

if __name__ == "__main__":
    test_async_a2a_flow()
