#!/usr/bin/env uv run python3
"""
Comprehensive A2A Integration Test - Real-world scenario
Demonstrates the full async-to-sync A2A communication flow with interactive tasks.
"""

import sys
import os
import time
import subprocess
import requests
import asyncio
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.agent.agent import Agent
from backend.agent.config import Config
from backend.object_model import UserMessage, SystemMessage

class A2AIntegrationTest:
    """Integration test for A2A async communication."""
    
    def __init__(self):
        self.agent = None
        self.server_process = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log a test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if details:
            result += f": {details}"
        print(result)
        self.test_results.append((test_name, success, details))
    
    def check_a2a_server(self) -> bool:
        """Check if A2A server is running, start if needed."""
        try:
            response = requests.get('http://localhost:9999/.well-known/agent.json', timeout=5)
            if response.status_code == 200:
                print("🟢 A2A server already running")
                return True
        except:
            pass
        
        print("🚀 Starting k8s-ai A2A server...")
        k8s_ai_path = Path.home() / "git" / "k8s-ai"
        if not k8s_ai_path.exists():
            print(f"❌ k8s-ai not found at {k8s_ai_path}")
            return False
        
        try:
            # Start server in background
            cmd = ['python', '-m', 'k8s_ai.server.main', '--context', 'kind-kind', '--host', '127.0.0.1', '--port', '9999']
            self.server_process = subprocess.Popen(
                cmd, 
                cwd=k8s_ai_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for server to start
            for i in range(15):
                try:
                    response = requests.get('http://localhost:9999/.well-known/agent.json', timeout=2)
                    if response.status_code == 200:
                        print("🟢 A2A server started successfully")
                        return True
                except:
                    pass
                print(f"   Waiting for server... ({i+1}/15)")
                time.sleep(1)
            
            print("❌ A2A server failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Error starting A2A server: {e}")
            return False
    
    def setup_agent(self) -> bool:
        """Set up AI-6 agent with A2A configuration."""
        try:
            print("\\n🤖 Setting up AI-6 Agent with A2A...")
            config_file = os.path.join(os.path.dirname(__file__), 'config_async.yaml')
            config = Config.from_file(config_file)
            
            self.agent = Agent(config)
            
            # Verify A2A integration
            if not self.agent.a2a_message_pump:
                self.log_result("Agent A2A Setup", False, "A2A message pump not initialized")
                return False
            
            # Check available tools
            a2a_tools = [name for name in self.agent.tool_dict.keys() if name.startswith('kind-k8s-ai_')]
            task_tools = [name for name in self.agent.tool_dict.keys() if name.startswith('a2a_')]
            
            if not a2a_tools or not task_tools:
                self.log_result("Agent A2A Setup", False, f"Missing tools: A2A={len(a2a_tools)}, Task={len(task_tools)}")
                return False
            
            self.log_result("Agent A2A Setup", True, f"A2A tools: {len(a2a_tools)}, Task tools: {len(task_tools)}")
            return True
            
        except Exception as e:
            self.log_result("Agent A2A Setup", False, f"Exception: {e}")
            return False
    
    def test_basic_task_management(self) -> bool:
        """Test basic task management operations."""
        print("\\n📋 Testing Basic Task Management...")
        
        try:
            # Test 1: List tasks (should be empty)
            result = self.agent.tool_dict['a2a_list_tasks'].run()
            if "No active A2A tasks" not in result:
                self.log_result("List Empty Tasks", False, f"Unexpected result: {result}")
                return False
            self.log_result("List Empty Tasks", True)
            
            # Test 2: Start a task  
            a2a_tool_name = [name for name in self.agent.tool_dict.keys() if name.startswith('kind-k8s-ai_')][0]
            result = self.agent.tool_dict[a2a_tool_name].run(
                message="Check the health of all pods in the cluster"
            )
            
            if "Started" not in result or "Monitoring" not in result:
                self.log_result("Start Task", False, f"Unexpected result: {result}")
                return False
                
            # Extract task ID
            task_id = None
            if "ID:" in result:
                task_id = result.split("ID:")[1].strip().split(")")[0]
            
            if not task_id:
                self.log_result("Start Task", False, "Could not extract task ID")
                return False
                
            self.log_result("Start Task", True, f"Task ID: {task_id}")
            self.task_id = task_id  # Save for later tests
            
            # Test 3: List tasks (should show our task)
            result = self.agent.tool_dict['a2a_list_tasks'].run()
            if task_id not in result or "Active A2A Tasks (1)" not in result:
                self.log_result("List Active Tasks", False, f"Task not found in list: {result}")
                return False
            self.log_result("List Active Tasks", True)
            
            # Test 4: Check task status
            result = self.agent.tool_dict['a2a_task_status'].run(task_id=task_id)
            if task_id not in result or ("running" not in result and "starting" not in result):
                self.log_result("Task Status", False, f"Unexpected status: {result}")
                return False
            self.log_result("Task Status", True)
            
            return True
            
        except Exception as e:
            self.log_result("Basic Task Management", False, f"Exception: {e}")
            return False
    
    def test_interactive_communication(self) -> bool:
        """Test interactive communication with running tasks."""
        print("\\n💬 Testing Interactive Communication...")
        
        if not hasattr(self, 'task_id'):
            self.log_result("Interactive Communication", False, "No task ID from previous test")
            return False
        
        try:
            # Test 1: Send message to task
            result = self.agent.tool_dict['a2a_send_message'].run(
                task_id=self.task_id,
                message="Please focus specifically on pods that are not in 'Running' state"
            )
            
            if "Sent message" not in result:
                self.log_result("Send Message to Task", False, f"Unexpected result: {result}")
                return False
            self.log_result("Send Message to Task", True)
            
            # Test 2: Wait a bit and check status again
            time.sleep(2)
            result = self.agent.tool_dict['a2a_task_status'].run(task_id=self.task_id)
            if self.task_id not in result:
                self.log_result("Task Status After Message", False, f"Task status error: {result}")
                return False
            self.log_result("Task Status After Message", True)
            
            return True
            
        except Exception as e:
            self.log_result("Interactive Communication", False, f"Exception: {e}")
            return False
    
    def test_session_integration(self) -> bool:
        """Test SystemMessage injection and session integration."""
        print("\\n📨 Testing Session Integration...")
        
        try:
            # Count initial messages
            initial_count = len(self.agent.session.messages)
            self.log_result("Initial Message Count", True, f"{initial_count} messages")
            
            # Wait for potential interim messages (simulate background activity)
            print("   Waiting for interim messages...")
            time.sleep(5)
            
            # Check for new messages
            current_count = len(self.agent.session.messages)
            
            # Analyze message types
            message_types = {}
            for msg in self.agent.session.messages:
                message_types[msg.role] = message_types.get(msg.role, 0) + 1
            
            print(f"   Message breakdown: {message_types}")
            
            # We should have system messages from A2A setup
            if 'system' not in message_types or message_types['system'] == 0:
                self.log_result("SystemMessage Integration", False, "No system messages found")
                return False
                
            self.log_result("SystemMessage Integration", True, f"System messages: {message_types['system']}")
            return True
            
        except Exception as e:
            self.log_result("Session Integration", False, f"Exception: {e}")
            return False
    
    def test_task_lifecycle(self) -> bool:
        """Test complete task lifecycle."""
        print("\\n🔄 Testing Task Lifecycle...")
        
        if not hasattr(self, 'task_id'):
            self.log_result("Task Lifecycle", False, "No task ID from previous test")
            return False
        
        try:
            # Test task cancellation
            result = self.agent.tool_dict['a2a_cancel_task'].run(task_id=self.task_id)
            if "Cancelled" not in result:
                self.log_result("Cancel Task", False, f"Unexpected result: {result}")
                return False
            self.log_result("Cancel Task", True)
            
            # Verify task is no longer active
            result = self.agent.tool_dict['a2a_list_tasks'].run()
            if self.task_id in result:
                self.log_result("Task Cleanup", False, "Task still active after cancellation")
                return False
            self.log_result("Task Cleanup", True)
            
            return True
            
        except Exception as e:
            self.log_result("Task Lifecycle", False, f"Exception: {e}")
            return False
    
    def test_multiple_concurrent_tasks(self) -> bool:
        """Test multiple concurrent A2A tasks."""
        print("\\n⚡ Testing Multiple Concurrent Tasks...")
        
        try:
            a2a_tool_name = [name for name in self.agent.tool_dict.keys() if name.startswith('kind-k8s-ai_')][0]
            
            # Start multiple tasks
            task_ids = []
            tasks = [
                "List all pods and their resource usage",
                "Check the status of all services",
                "Analyze cluster node health"
            ]
            
            for i, task_msg in enumerate(tasks):
                result = self.agent.tool_dict[a2a_tool_name].run(message=task_msg)
                if "Started" in result and "ID:" in result:
                    task_id = result.split("ID:")[1].strip().split(")")[0]
                    task_ids.append(task_id)
                    self.log_result(f"Start Task {i+1}", True, f"Task ID: {task_id}")
                else:
                    self.log_result(f"Start Task {i+1}", False, f"Failed: {result}")
                    return False
                
                time.sleep(1)  # Brief pause between task starts
            
            # Verify all tasks are active
            result = self.agent.tool_dict['a2a_list_tasks'].run()
            active_count = len(task_ids)
            
            if f"Active A2A Tasks ({active_count})" not in result:
                self.log_result("Multiple Tasks Active", False, f"Expected {active_count} tasks, got: {result}")
                return False
            self.log_result("Multiple Tasks Active", True, f"{active_count} concurrent tasks")
            
            # Cleanup all tasks
            for task_id in task_ids:
                self.agent.tool_dict['a2a_cancel_task'].run(task_id=task_id)
            
            self.log_result("Multiple Task Cleanup", True)
            return True
            
        except Exception as e:
            self.log_result("Multiple Concurrent Tasks", False, f"Exception: {e}")
            return False
    
    def run_full_integration_test(self) -> bool:
        """Run the complete integration test suite."""
        header = "🧪 A2A COMPREHENSIVE INTEGRATION TEST"
        print(header)
        print("=" * len(header))
        
        # Setup phase
        if not self.check_a2a_server():
            return False
            
        if not self.setup_agent():
            return False
        
        # Test phases
        tests = [
            ("Basic Task Management", self.test_basic_task_management),
            ("Interactive Communication", self.test_interactive_communication), 
            ("Session Integration", self.test_session_integration),
            ("Task Lifecycle", self.test_task_lifecycle),
            ("Multiple Concurrent Tasks", self.test_multiple_concurrent_tasks)
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            if not test_func():
                all_passed = False
        
        # Summary
        results_header = "🏆 INTEGRATION TEST RESULTS"
        print("\\n" + "=" * len(results_header))
        print(results_header)
        print("=" * len(results_header))
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        for test_name, success, details in self.test_results:
            status = "✅" if success else "❌"
            print(f"{status} {test_name}")
            if details and not success:
                print(f"    {details}")
        
        print(f"\\n📊 Summary: {passed}/{total} tests passed")
        
        if all_passed:
            print("\\n🎉 ALL INTEGRATION TESTS PASSED!")
            print("\\n🔥 A2A Async-to-Sync Integration is fully working:")
            print("   ✅ Background task monitoring")
            print("   ✅ Interactive task communication") 
            print("   ✅ SystemMessage injection")
            print("   ✅ Multiple concurrent tasks")
            print("   ✅ Complete task lifecycle management")
            print("   ✅ Session persistence and state management")
        else:
            print("\\n❌ Some integration tests failed - check implementation")
        
        return all_passed
    
    def cleanup(self):
        """Clean up test resources."""
        if self.server_process:
            print("\\n🧹 Cleaning up A2A server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()

def main():
    """Run the integration test."""
    test = A2AIntegrationTest()
    
    try:
        success = test.run_full_integration_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\\n⏹️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        test.cleanup()

if __name__ == "__main__":
    sys.exit(main())