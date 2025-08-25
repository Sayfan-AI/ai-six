#!/usr/bin/env uv run python3
"""
A2A Async Communication Demo
Demonstrates real-world usage of A2A async-to-sync communication in AI-6.
"""

import sys
import os
import time
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.agent.agent import Agent
from backend.agent.config import Config

def simulate_user_interaction():
    """Simulate a realistic user interaction with A2A async capabilities."""
    
    demo_header = "🎭 A2A Async Communication Demo"
    print(demo_header)
    print("=" * len(demo_header))
    print("This demo simulates a user interacting with AI-6 using A2A agents")
    print("for long-running Kubernetes operations.\\n")
    
    # Load configuration
    config_file = os.path.join(os.path.dirname(__file__), 'config_async.yaml')
    config = Config.from_file(config_file)
    
    # Create agent
    print("👤 User: Setting up AI-6 with A2A capabilities...")
    agent = Agent(config)
    
    if not agent.a2a_message_pump:
        print("❌ A2A not available - please ensure a2a-sdk is installed and server is running")
        return
    
    print(f"✅ AI-6 Agent ready with {len(agent.tool_dict)} tools")
    
    # Find A2A tools
    a2a_tools = [name for name in agent.tool_dict.keys() if name.startswith('kind-k8s-ai_')]
    if not a2a_tools:
        print("❌ No A2A operation tools found - is the A2A server running?")
        return
    
    kubectl_tool = a2a_tools[0]
    print(f"🔧 Using A2A tool: {kubectl_tool}\\n")
    
    # Scenario: User starts a long-running analysis
    print("👤 User: I need a comprehensive security analysis of our Kubernetes cluster")
    print("🤖 AI-6: Starting comprehensive security analysis...")
    
    result = agent.tool_dict[kubectl_tool].run(
        message="Perform a comprehensive security analysis of the Kubernetes cluster. Check for vulnerabilities, misconfigurations, and security best practices. This should include pod security contexts, RBAC analysis, network policies, and resource limits."
    )
    
    print(f"🤖 AI-6: {result}")
    
    # Extract task ID for interaction
    task_id = None
    if "ID:" in result:
        task_id = result.split("ID:")[1].strip().split(")")[0]
    
    if not task_id:
        print("❌ Could not extract task ID")
        return
    
    # Show that user can do other things immediately
    async_header = "⚡ ASYNC BENEFIT: User can multitask immediately!"
    print("\\n" + "=" * len(async_header))
    print(async_header)
    print("=" * len(async_header))
    
    print("\\n👤 User: While that's running, let me check what tasks are active")
    result = agent.tool_dict['a2a_list_tasks'].run()
    print(f"🤖 AI-6: {result}")
    
    print("\\n👤 User: What's the detailed status of my security analysis?")
    result = agent.tool_dict['a2a_task_status'].run(task_id=task_id)
    print(f"🤖 AI-6: {result}")
    
    # Simulate interim updates (in real usage these would come from A2A agent)
    updates_header = "📨 BACKGROUND UPDATES (via SystemMessages)"
    print("\\n" + "=" * len(updates_header)) 
    print(updates_header)
    print("=" * len(updates_header))
    
    # Simulate A2A interim messages
    from backend.object_model import SystemMessage
    
    interim_updates = [
        "Security scan 25% complete - analyzing pod security contexts...",
        "Found 3 pods without security contexts - continuing analysis...",
        "RBAC analysis complete - 2 overprivileged service accounts found...",
        "Network policy scan complete - 5 pods without network restrictions..."
    ]
    
    for i, update in enumerate(interim_updates):
        time.sleep(2)  # Simulate time passing
        system_msg = SystemMessage(content=f"A2A Task Update [{task_id}]: {update}")
        agent.session.add_message(system_msg)
        print(f"🤖 AI-6: [Background Update] {update}")
        
        if i == 1:  # User responds to an update
            print("\\n👤 User: Focus the analysis on the pods without security contexts")
            result = agent.tool_dict['a2a_send_message'].run(
                task_id=task_id,
                message="Please prioritize the analysis of pods without security contexts. Provide detailed recommendations for fixing these security issues."
            )
            print(f"🤖 AI-6: {result}")
    
    # User can do other work
    print("\\n👤 User: Let me start another task while the security analysis continues")
    
    result = agent.tool_dict[kubectl_tool].run(
        message="Check the resource usage and performance metrics for all nodes in the cluster"
    )
    print(f"🤖 AI-6: {result}")
    
    # Check multiple active tasks
    print("\\n👤 User: Show me all my active tasks now")
    result = agent.tool_dict['a2a_list_tasks'].run()
    print(f"🤖 AI-6: {result}")
    
    # Simulate completion
    time.sleep(3)
    
    completion_header = "✅ TASK COMPLETION"
    print("\\n" + "=" * len(completion_header))
    print(completion_header)
    print("=" * len(completion_header))
    
    # Simulate final result
    final_result = SystemMessage(content=f"A2A Task Complete [{task_id}]: Security analysis complete! Found 5 critical issues, 8 warnings. Detailed report with remediation steps available. Key findings: 3 pods without security contexts, 2 overprivileged service accounts, 5 pods without network policies.")
    agent.session.add_message(final_result)
    print("🤖 AI-6: Security analysis complete! Found 5 critical issues, 8 warnings. Here are the key findings and remediation steps...")
    
    # Final status
    print("\\n👤 User: Great! Let me clean up the completed tasks")
    result = agent.tool_dict['a2a_cancel_task'].run(task_id=task_id)
    print(f"🤖 AI-6: {result}")
    
    # Show session summary
    summary_header = "📈 SESSION SUMMARY"
    print("\\n" + "=" * len(summary_header))
    print(summary_header)
    print("=" * len(summary_header))
    
    message_types = {}
    for msg in agent.session.messages:
        message_types[msg.role] = message_types.get(msg.role, 0) + 1
    
    print(f"Total messages in session: {len(agent.session.messages)}")
    for role, count in message_types.items():
        print(f"  {role}: {count}")
    
    print("\\n🎉 Demo Complete!")
    print("\\n🔥 Key A2A Features Demonstrated:")
    print("   ✅ Immediate task start with background execution")
    print("   ✅ Real-time interim updates via SystemMessages")  
    print("   ✅ Interactive communication with running tasks")
    print("   ✅ Multitasking - multiple concurrent operations")
    print("   ✅ Complete task lifecycle management")
    print("   ✅ Session integration with message persistence")
    
    print("\\n💡 User Benefits:")
    print("   • Never blocked waiting for long-running operations")
    print("   • Real-time progress updates and notifications")
    print("   • Can respond to questions and provide clarifications")
    print("   • Manage multiple AI agents simultaneously")
    print("   • Full conversation history including background updates")

if __name__ == "__main__":
    try:
        simulate_user_interaction()
    except KeyboardInterrupt:
        print("\\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\\n💥 Demo failed: {e}")
        import traceback
        traceback.print_exc()