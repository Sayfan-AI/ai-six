#!/usr/bin/env python3
"""Proper test for A2A async communication flow with actual assertions."""

import sys
import os
import asyncio
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.agent.agent import Agent
from backend.agent.config import Config

def test_async_a2a_flow():
    """Test the full async A2A communication flow with proper assertions."""
    
    print("🧪 Testing A2A Async Communication Flow (with assertions)")
    print("=" * 50)
    
    # Track test failures
    failures = []
    
    # Load config with A2A server configuration
    config_file = os.path.join(os.path.dirname(__file__), 'config.yaml')
    config = Config.from_file(config_file)
    
    print("✅ Configuration loaded")
    print(f"   A2A servers: {len(config.a2a_servers)}")
    
    # Test 1: Verify A2A servers are configured
    if len(config.a2a_servers) == 0:
        failures.append("❌ Test 1: No A2A servers configured")
    else:
        print("✅ Test 1: A2A servers configured")
    
    # Create agent
    print("\n🤖 Creating AI-6 agent with A2A async support...")
    agent = Agent(config)
    print(f"Agent created with {len(agent.tool_dict)} tools")
    
    # Test 2: Verify A2A tools are discovered
    a2a_tools = [name for name in agent.tool_dict.keys() if name.startswith('kind-k8s-ai_')]
    task_tools = [name for name in agent.tool_dict.keys() if name.startswith('a2a_')]
    
    if len(a2a_tools) == 0:
        failures.append("❌ Test 2: No A2A operation tools discovered")
        print("❌ Test 2: No A2A operation tools discovered")
        print("   (Is the A2A server running at localhost:9999?)")
        # Can't continue without A2A tools
        return len(failures) == 0
    else:
        print(f"✅ Test 2: Found {len(a2a_tools)} A2A operation tools")
    
    if len(task_tools) < 4:
        failures.append(f"❌ Test 3: Expected 4 task management tools, found {len(task_tools)}")
    else:
        print(f"✅ Test 3: Found {len(task_tools)} task management tools")
    
    # Test 4: Verify initial state (no active tasks)
    print("\n📝 Test 4: Checking initial state...")
    if 'a2a_list_tasks' in agent.tool_dict:
        result = agent.tool_dict['a2a_list_tasks'].run()
        if "No active A2A tasks" not in result:
            failures.append(f"❌ Test 4: Expected no active tasks, got: {result}")
        else:
            print("✅ Test 4: No active tasks initially")
    else:
        failures.append("❌ Test 4: a2a_list_tasks tool not found")
    
    # Test 5: Start an A2A task
    print("\n🚀 Test 5: Starting A2A task...")
    a2a_tool_name = a2a_tools[0]
    task_id = None
    
    try:
        result = agent.tool_dict[a2a_tool_name].run(
            message="Show me the current status of all pods in the cluster"
        )
        
        if "Started" in result and "ID:" in result:
            task_id = result.split("ID:")[1].strip().split(")")[0]
            print(f"✅ Test 5: Task started with ID: {task_id}")
        else:
            failures.append(f"❌ Test 5: Unexpected start result: {result}")
            
    except Exception as e:
        failures.append(f"❌ Test 5: Failed to start A2A task: {e}")
    
    if not task_id:
        print("❌ Cannot continue without task ID")
        return len(failures) == 0
    
    # Test 6: Verify task appears in active tasks
    print("\n📝 Test 6: Verifying task is active...")
    result = agent.tool_dict['a2a_list_tasks'].run()
    if task_id in result:
        print(f"✅ Test 6: Task {task_id} is listed as active")
    else:
        failures.append(f"❌ Test 6: Task {task_id} not found in active tasks")
    
    # Test 7: Wait for interim messages (THE KEY TEST)
    print("\n⏳ Test 7: Checking for interim messages...")
    print("Waiting 10 seconds for background messages...")
    
    initial_message_count = len(agent.session.messages)
    messages_received = False
    
    for i in range(10):
        time.sleep(1)
        current_message_count = len(agent.session.messages)
        if current_message_count > initial_message_count:
            messages_received = True
            new_messages = current_message_count - initial_message_count
            print(f"✅ Test 7: Received {new_messages} interim message(s)")
            for msg in agent.session.messages[initial_message_count:]:
                print(f"   Message: {msg.role}: {msg.content[:100]}...")
            break
        else:
            print(f"   Waiting... ({i+1}/10) - No messages yet")
    
    if not messages_received:
        failures.append("❌ Test 7: No interim messages received (monitoring not working)")
        print("❌ Test 7: No interim messages received")
        print("   Note: The k8s-ai A2A server doesn't support SSE streaming")
        print("   It returns application/json instead of text/event-stream")
        print("   This means all responses come back at once, not streamed")
    
    # Test 8: Send message to task
    print("\n💬 Test 8: Sending message to task...")
    try:
        result = agent.tool_dict['a2a_send_message'].run(
            task_id=task_id,
            message="Please focus on pods that are not in 'Running' status"
        )
        if "Sent message" in result:
            print(f"✅ Test 8: Message sent successfully")
        else:
            failures.append(f"❌ Test 8: Unexpected send result: {result}")
    except Exception as e:
        failures.append(f"❌ Test 8: Failed to send message: {e}")
    
    # Test 9: Check task status
    print("\n📊 Test 9: Checking task status...")
    if 'a2a_task_status' in agent.tool_dict:
        try:
            result = agent.tool_dict['a2a_task_status'].run(task_id=task_id)
            if task_id in result:
                # Check if status shows task is actually running
                if "Status: starting" in result:
                    failures.append("❌ Test 9: Task still in 'starting' status after 10+ seconds")
                    print("❌ Test 9: Task stuck in 'starting' status")
                elif "Status: running" in result:
                    print("✅ Test 9: Task is running")
                else:
                    print(f"⚠️ Test 9: Unknown status in: {result}")
            else:
                failures.append(f"❌ Test 9: Task status doesn't contain task ID")
        except Exception as e:
            failures.append(f"❌ Test 9: Failed to check status: {e}")
    
    # Test 10: Cancel task
    print("\n🧹 Test 10: Canceling task...")
    if 'a2a_cancel_task' in agent.tool_dict:
        try:
            result = agent.tool_dict['a2a_cancel_task'].run(task_id=task_id)
            if "Cancelled" in result:
                print("✅ Test 10: Task cancelled successfully")
            else:
                failures.append(f"❌ Test 10: Unexpected cancel result: {result}")
        except Exception as e:
            failures.append(f"❌ Test 10: Failed to cancel task: {e}")
    
    # Print test summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    if failures:
        print(f"\n❌ {len(failures)} test(s) failed:")
        for failure in failures:
            print(f"   {failure}")
        print("\n⚠️ ISSUES FOUND:")
        print("   1. k8s-ai A2A server doesn't support SSE streaming")
        print("   2. Server returns JSON responses instead of event streams")
        print("   3. All responses come back at once after processing")
        print("   4. No real-time progress updates are possible with this server")
    else:
        print("\n✅ All tests passed!")
    
    return len(failures) == 0

if __name__ == "__main__":
    success = test_async_a2a_flow()
    sys.exit(0 if success else 1)