#!/usr/bin/env uv run python3
"""
Quick test to verify A2A tasks start immediately and don't block UI.
This test specifically checks that task creation returns immediately.
"""

import sys
import os
import time
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.agent.agent import Agent
from backend.agent.config import Config

def test_immediate_response():
    """Test that A2A task creation returns immediately."""
    print("🚀 Testing A2A Task Responsiveness")
    print("=" * 35)
    
    # Setup agent
    config_file = os.path.join(os.path.dirname(__file__), 'config_async.yaml')
    config = Config.from_file(config_file)
    agent = Agent(config)
    
    if not agent.a2a_message_pump:
        print("❌ A2A not available")
        return False
    
    # Find A2A tool
    a2a_tools = [name for name in agent.tool_dict.keys() if name.startswith('kind-k8s-ai_')]
    if not a2a_tools:
        print("❌ No A2A tools found")
        return False
    
    kubectl_tool = a2a_tools[0]
    
    # Test immediate response time
    print(f"⏱️  Testing response time for A2A task creation...")
    
    start_time = time.time()
    result = agent.tool_dict[kubectl_tool].run(
        message="Perform a quick health check of the cluster"
    )
    end_time = time.time()
    
    response_time = end_time - start_time
    print(f"📊 Response time: {response_time:.2f} seconds")
    
    # Check that response is immediate (should be < 1 second for task creation)
    if response_time > 2.0:
        print(f"❌ Response too slow: {response_time:.2f}s (expected < 2s)")
        return False
    
    # Check that we got a proper task ID response
    if "Started" not in result or "Monitoring" not in result:
        print(f"❌ Unexpected response: {result}")
        return False
    
    print(f"✅ Task created immediately in {response_time:.2f}s")
    print(f"✅ Response: {result}")
    
    # Extract task ID and clean up
    if "ID:" in result:
        task_id = result.split("ID:")[1].strip().split(")")[0]
        print(f"🧹 Cleaning up task {task_id}")
        agent.tool_dict['a2a_cancel_task'].run(task_id=task_id)
    
    print("\n🎉 Responsiveness test PASSED!")
    print("✅ A2A tasks start immediately without blocking UI")
    
    return True

if __name__ == "__main__":
    try:
        success = test_immediate_response()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)