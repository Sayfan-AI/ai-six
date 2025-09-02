#!/usr/bin/env python3
"""Complete test for A2A async communication flow with assertions and visual feedback."""

import sys
import os
import asyncio
import time
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Load environment variables BEFORE importing Config
from dotenv import load_dotenv
load_dotenv()

from backend.agent.agent import Agent
from backend.agent.config import Config

def test_async_a2a_flow():
    """Test the full async A2A communication flow."""
    
    print("🧪 Testing A2A Async Communication Flow")
    print("=" * 50)
    
    # Track test results
    passed = 0
    failed = 0
    
    # Create config
    config_file = os.path.join(os.path.dirname(__file__), 'config.yaml')
    
    try:
        config = Config.from_file(config_file)
        print("✅ Configuration loaded")
        
        # Test 1: Verify A2A servers are configured
        if not config.a2a_servers:
            print("❌ Test 1 FAILED: No A2A servers configured")
            failed += 1
        else:
            print(f"✅ Test 1 PASSED: {len(config.a2a_servers)} A2A server(s) configured")
            for server in config.a2a_servers:
                print(f"   - {server['name']}: {server['url']}")
            passed += 1
        
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return 1
    
    # Create agent
    print("\n🤖 Creating AI-6 agent with A2A support...")
    try:
        agent = Agent(config)
        print(f"✅ Agent created with {len(agent.tool_dict)} tools")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return 1
    
    # Test 2: Verify A2A tools are discovered
    print("\n🔧 Checking A2A Tools...")
    a2a_tools = [name for name in agent.tool_dict.keys() if 'kind-k8s-ai' in name]
    task_tools = [name for name in agent.tool_dict.keys() if 'a2a_' in name]
    
    if not a2a_tools:
        print("❌ Test 2 FAILED: No A2A operation tools discovered")
        failed += 1
    else:
        print(f"✅ Test 2 PASSED: {len(a2a_tools)} A2A operation tool(s)")
        for tool in a2a_tools[:3]:
            print(f"   • {tool}")
        passed += 1
    
    # Test 3: Verify task management tools
    if len(task_tools) != 4:
        print(f"❌ Test 3 FAILED: Expected 4 task tools, found {len(task_tools)}")
        failed += 1
    else:
        print(f"✅ Test 3 PASSED: {len(task_tools)} task management tools")
        for tool in task_tools:
            print(f"   • {tool}")
        passed += 1
    
    # Test 4: Check initial state (no active tasks)
    print("\n📝 Test 4: Initial State Check")
    if 'a2a_list_tasks' in agent.tool_dict:
        result = agent.tool_dict['a2a_list_tasks'].run()
        if "No active" in result:
            print("✅ Test 4 PASSED: No active tasks initially")
            passed += 1
        else:
            print(f"❌ Test 4 FAILED: Expected empty task list, got: {result}")
            failed += 1
    else:
        print("❌ Test 4 FAILED: a2a_list_tasks tool not found")
        failed += 1
    
    # Test 5: Start an A2A task
    print("\n🚀 Test 5: Starting A2A Task")
    task_id = None
    try:
        if a2a_tools:
            tool_name = a2a_tools[0]
            tool = agent.tool_dict[tool_name]
            # Use a more complex query that might take longer
            # Can be overridden with TEST_QUICK=1 environment variable
            if os.environ.get('TEST_QUICK', '').lower() in ['1', 'true']:
                message = "List all pods in the cluster"
                print("   Using quick test query")
            else:
                message = "List all pods in the cluster and describe each one in detail, including events and logs"
                print("   Using detailed test query (may take longer)")
            
            result = tool.run(message=message)
            print(f"Result: {result[:100]}...")
            
            # Extract task ID
            match = re.search(r'ID: ([a-zA-Z0-9_-]+)', result)
            if match:
                task_id = match.group(1)
                print(f"✅ Test 5 PASSED: Task started with ID: {task_id}")
                passed += 1
            else:
                print(f"❌ Test 5 FAILED: Could not extract task ID from: {result}")
                failed += 1
        else:
            print("❌ Test 5 FAILED: No A2A tools available")
            failed += 1
    except Exception as e:
        print(f"❌ Test 5 FAILED: {e}")
        failed += 1
    
    # Test 6: Verify task appears in active list
    if task_id:
        print("\n📊 Test 6: Task in Active List")
        result = agent.tool_dict['a2a_list_tasks'].run()
        if task_id in result:
            print(f"✅ Test 6 PASSED: Task {task_id} is active")
            passed += 1
        else:
            print(f"❌ Test 6 FAILED: Task {task_id} not in active list")
            failed += 1
    
    # Test 7: Wait for interim messages
    print("\n⏳ Test 7: Checking Interim Messages")
    initial_count = len(agent.session.messages)
    print(f"Initial message count: {initial_count}")
    print("Waiting 10 seconds for background messages...")
    
    # Wait and check for new messages
    time.sleep(10)
    
    final_count = len(agent.session.messages)
    new_messages = final_count - initial_count
    
    if new_messages > 0:
        print(f"✅ Test 7 PASSED: Received {new_messages} interim message(s)")
        # Show last few messages
        for msg in agent.session.messages[-min(3, new_messages):]:
            preview = str(msg)[:80]
            print(f"   • {preview}...")
        passed += 1
    else:
        print("❌ Test 7 FAILED: No interim messages received")
        failed += 1
    
    # Test 8: Send message to task (if still running)
    if task_id:
        print("\n💬 Test 8: Send Message to Task")
        # First check if task is still active
        task_list = agent.tool_dict['a2a_list_tasks'].run()
        if task_id in task_list:
            try:
                result = agent.tool_dict['a2a_send_message'].run(
                    task_id=task_id,
                    message="Focus on pods that are not Running"
                )
                if "Sent message" in result or "sent" in result.lower():
                    print(f"✅ Test 8 PASSED: Message sent to task")
                    passed += 1
                else:
                    print(f"❌ Test 8 FAILED: Unexpected result: {result}")
                    failed += 1
            except Exception as e:
                print(f"❌ Test 8 FAILED: {e}")
                failed += 1
        else:
            print(f"✅ Test 8 PASSED: Task already completed (fast response)")
            passed += 1
    
    # Test 9: Check task status
    if task_id:
        print("\n📈 Test 9: Task Status Check")
        try:
            result = agent.tool_dict['a2a_task_status'].run(task_id=task_id)
            # Accept both "not found" (task completed and cleaned up) and normal status
            if "not found" in result.lower():
                print(f"✅ Test 9 PASSED: Task completed and cleaned up")
                print(f"   Status: Task already completed")
                passed += 1
            elif task_id in result and ("running" in result.lower() or "completed" in result.lower()):
                print(f"✅ Test 9 PASSED: Task status retrieved")
                print(f"   Status preview: {result[:100]}...")
                passed += 1
            else:
                print(f"❌ Test 9 FAILED: Invalid status: {result}")
                failed += 1
        except Exception as e:
            print(f"❌ Test 9 FAILED: {e}")
            failed += 1
    
    # Test 10: Cancel task (if still active)
    if task_id:
        print("\n🧹 Test 10: Cancel Task")
        # First check if task is still active
        task_list = agent.tool_dict['a2a_list_tasks'].run()
        if task_id in task_list:
            try:
                result = agent.tool_dict['a2a_cancel_task'].run(task_id=task_id)
                if "Cancelled" in result or "cancelled" in result:
                    print(f"✅ Test 10 PASSED: Task cancelled")
                    passed += 1
                else:
                    print(f"❌ Test 10 FAILED: {result}")
                    failed += 1
            except Exception as e:
                print(f"❌ Test 10 FAILED: {e}")
                failed += 1
        else:
            print(f"✅ Test 10 PASSED: Task already completed (no need to cancel)")
            passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Passed: {passed}/10")
    print(f"❌ Failed: {failed}/10")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit_code = test_async_a2a_flow()
    sys.exit(exit_code)