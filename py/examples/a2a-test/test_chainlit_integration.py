#!/usr/bin/env uv run python3
"""
Chainlit Integration Test - Simulates exactly what happens in Chainlit UI
This test replicates the Chainlit message handling flow to identify blocking issues.
"""

import sys
import os
import time
import asyncio
import threading
import traceback
from unittest.mock import Mock, patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from backend.agent.agent import Agent
from backend.agent.config import Config

class MockChainlitMessage:
    """Mock Chainlit message for testing."""
    def __init__(self, content=""):
        self.content = content
        self._tokens = []
    
    async def send(self):
        print(f"📤 Mock message sent")
    
    async def stream_token(self, token: str):
        self._tokens.append(token)
        print(f"📝 Streaming token: {token[:50]}{'...' if len(token) > 50 else ''}")
    
    async def update(self):
        print(f"✅ Mock message updated - total tokens: {len(self._tokens)}")

class ChainlitIntegrationTest:
    """Test that simulates Chainlit's exact message handling flow."""
    
    def __init__(self):
        self.agent = None
        self.ui_blocked = False
        self.response_times = []
        
    def setup_agent(self):
        """Set up the agent like Chainlit does."""
        print("🤖 Setting up AI-6 Agent for Chainlit simulation...")
        config_file = os.path.join(os.path.dirname(__file__), 'config_async.yaml')
        config = Config.from_file(config_file)
        self.agent = Agent(config)

        print(f"✅ Agent ready with {len(self.agent.tool_dict)} tools")
        return True
    
    async def simulate_chainlit_message_handler(self, user_message: str):
        """Simulate exactly what Chainlit's on_message handler does."""
        print(f"\n📨 Simulating Chainlit message handler for: '{user_message}'")
        
        # This simulates the exact Chainlit on_message flow
        enabled_tool_ids = [k for k in self.agent.tool_dict.keys()]
        
        # Streaming mode (what Chainlit does)
        msg = MockChainlitMessage(content="")
        await msg.send()

        # Define a callback function to handle streaming chunks
        async def on_chunk(chunk: str):
            # Use the mock streaming method
            await msg.stream_token(chunk)

        # Track timing like a real UI would
        start_time = time.time()
        
        # This is the exact call Chainlit makes
        try:
            print("🚀 Starting agent.stream_message (this should not block)...")
            
            # This simulates the blocking issue - if this call blocks,
            # the UI would be unresponsive
            self.agent.stream_message(
                user_message,
                self.agent.default_model_id,
                on_chunk_func=lambda chunk: asyncio.create_task(on_chunk(chunk)),
                available_tool_ids=enabled_tool_ids,
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            self.response_times.append(response_time)
            
            print(f"⏱️ stream_message completed in {response_time:.2f}s")
            
            # Mark the message as complete
            await msg.update()
            
            return response_time
            
        except Exception as e:
            print(f"❌ Error in message handler: {e}")
            raise
    
    async def test_ui_responsiveness(self):
        """Test if the UI remains responsive during A2A operations."""
        print("\n🧪 Testing UI Responsiveness During A2A Operations")
        print("=" * 55)
        
        # Test 1: Start A2A task and measure response time
        print("Test 1: A2A Task Creation Response Time")
        response_time = await self.simulate_chainlit_message_handler(
            "Use the kind-k8s-ai_kubectl_operations tool to show me all pods in the cluster"
        )
        
        # A2A tool operations include: LLM call + tool decision + tool execution + response
        # This reasonably takes 5-10 seconds depending on LLM speed
        if response_time > 10.0:
            print(f"❌ BLOCKING DETECTED: stream_message took {response_time:.2f}s (expected < 10s for A2A operations)")
            return False
        else:
            print(f"✅ RESPONSIVE: stream_message took {response_time:.2f}s")
        
        # Test 2: Simulate concurrent user interactions
        print("\nTest 2: Concurrent User Interactions")
        
        tasks = []
        for i in range(3):
            task = asyncio.create_task(
                self.simulate_chainlit_message_handler(f"Quick question {i+1}: Use a2a_task_status to check task status")
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        avg_response_time = sum(results) / len(results)
        print(f"📊 Average concurrent response time: {avg_response_time:.2f}s")
        
        # Concurrent operations might be slower due to LLM contention
        if avg_response_time > 10.0:
            print(f"❌ BLOCKING DETECTED: Concurrent operations too slow (avg: {avg_response_time:.2f}s)")
            return False
        else:
            print(f"✅ RESPONSIVE: Concurrent operations performed well")
        
        return True
    
    async def test_background_task_interaction(self):
        """Test interaction with background A2A tasks."""
        print("\nTest 3: Background Task Interaction")
        
        # Start a task
        response_time = await self.simulate_chainlit_message_handler(
            "Use the kind-k8s-ai_kubectl_operations tool to monitor cluster health"
        )
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Try to interact with tasks
        list_response_time = await self.simulate_chainlit_message_handler(
            "Use the a2a_list_tasks tool to show active tasks"
        )
        
        # Listing tasks still requires LLM to understand and execute
        if list_response_time > 8.0:
            print(f"❌ BLOCKING: Task listing took {list_response_time:.2f}s (expected < 8s)")
            return False
        
        print(f"✅ Task listing responsive: {list_response_time:.2f}s")
        return True
    
    async def simulate_ui_event_loop_interference(self):
        """Test if our A2A code interferes with the UI event loop."""
        print("\nTest 4: Event Loop Interference Detection")
        
        async def ui_task():
            """Simulate a UI task that should not be blocked."""
            for i in range(5):
                await asyncio.sleep(0.1)
                print(f"UI task heartbeat {i+1}/5")
        
        async def a2a_task():
            """Simulate A2A operation during UI task."""
            await self.simulate_chainlit_message_handler("Use the a2a_list_tasks tool")
        
        # Run the test
        start_time = time.time()
        
        # These should run concurrently without blocking
        ui_future = asyncio.create_task(ui_task())
        a2a_future = asyncio.create_task(a2a_task())
        
        await asyncio.gather(ui_future, a2a_future)
        
        end_time = time.time()
        
        total_time = end_time - start_time
        print(f"⏱️ Total concurrent execution time: {total_time:.2f}s")
        
        if total_time > 5.0:  # Should complete in ~0.5s if truly concurrent
            print("❌ BLOCKING: UI and A2A tasks did not run concurrently")
            return False
        
        print("✅ CONCURRENT: UI and A2A tasks ran properly in parallel")
        return True
    
    async def run_comprehensive_test(self):
        """Run all Chainlit integration tests."""
        print("🔬 CHAINLIT A2A INTEGRATION COMPREHENSIVE TEST")
        print("=" * 52)
        
        if not self.setup_agent():
            return False
        
        tests = [
            ("UI Responsiveness", self.test_ui_responsiveness()),
            ("Background Task Interaction", self.test_background_task_interaction()),
            ("Event Loop Interference", self.simulate_ui_event_loop_interference()),
        ]
        
        results = []
        for test_name, test_coro in tests:
            print(f"\n🧪 Running {test_name}...")
            try:
                result = await test_coro
                results.append((test_name, result))
                print(f"{'✅ PASS' if result else '❌ FAIL'}: {test_name}")
            except Exception as e:
                print(f"❌ FAIL: {test_name} - {e}")
                results.append((test_name, False))
        
        # Event loop test is now included in the tests list above
        
        # Summary
        print("\n" + "=" * 52)
        print("🏆 CHAINLIT INTEGRATION TEST RESULTS")
        print("=" * 52)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n📊 Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL CHAINLIT INTEGRATION TESTS PASSED!")
            print("✅ Chainlit UI should work smoothly with A2A operations")
        else:
            print("\n❌ SOME TESTS FAILED - Chainlit UI will likely be blocked")
            print("💡 The failing tests indicate the exact source of UI blocking")
        
        return passed == total

async def main():
    """Run the Chainlit integration test."""
    test = ChainlitIntegrationTest()
    
    try:
        success = await test.run_comprehensive_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)
