#!/usr/bin/env python3
"""
Debug script to test send_message_to_task functionality
"""

import sys
import os
import asyncio
import logging
import traceback
from pathlib import Path
from datetime import datetime

# Set up logging first
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.agent.agent import Agent
from backend.agent.config import Config
from backend.a2a_client.a2a_message_pump import A2ATaskInfo

async def main():
    """Test just the send_message_to_task functionality."""
    
    # Enable debug logging for A2A components
    logging.getLogger('backend.a2a_client.a2a_client').setLevel(logging.DEBUG)
    logging.getLogger('backend.a2a_client.a2a_message_pump').setLevel(logging.DEBUG)
    
    print("🧪 DEBUG SEND MESSAGE TEST")
    print("=" * 30)
    
    try:
        # Set up agent
        config_file = os.path.join(os.path.dirname(__file__), 'config_async.yaml')
        config = Config.from_file(config_file)
        agent = Agent(config)
        
        print("✅ Agent setup complete")
        
        # Check what tools we have
        print(f"Available A2A tools: {[name for name in agent.tool_dict.keys() if 'a2a' in name]}")
        
        # Since A2A server tools aren't discovered, let's manually test the send_message function
        # First create a fake task manually for testing
        if agent.a2a_message_pump:
            # Add a fake task to test send_message
            fake_task_id = "test-task-123"
            fake_task_info = A2ATaskInfo(
                task_id=fake_task_id,
                server_name="kind-k8s-ai",
                skill_id="kubectl_operations", 
                status="running",
                created_at=datetime.now(),
                last_checked=datetime.now()
            )
            
            agent.a2a_message_pump.active_tasks[fake_task_id] = fake_task_info
            print(f"✅ Created fake task: {fake_task_id}")
            
            # Now test send_message
            print(f"🧪 Testing send_message_to_task...")
            result = agent.tool_dict['a2a_send_message'].run(
                task_id=fake_task_id,
                message="Please focus specifically on pods that are not in 'Running' state"
            )
            
            print(f"✅ Send message result: {result}")
        else:
            print("❌ No A2A message pump found")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())