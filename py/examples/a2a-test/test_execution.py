#!/usr/bin/env python3
"""Test A2A tool execution."""

import sys
import os
import traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.agent.agent import Agent
from backend.agent.config import Config

def test_a2a_execution():
    """Test executing an A2A tool."""
    
    print("Testing A2A Tool Execution")
    print("=" * 30)
    
    # Load config with A2A server configuration
    config_file = os.path.join(os.path.dirname(__file__), 'config.yaml')
    config = Config.from_file(config_file)
    
    # Create agent
    agent = Agent(config)
    
    # Find the A2A tool
    a2a_tool_name = 'kind-k8s-ai_kubectl_operations'
    
    if a2a_tool_name not in agent.tool_dict:
        print(f"❌ A2A tool {a2a_tool_name} not found in agent tools")
        return
    
    tool = agent.tool_dict[a2a_tool_name]
    print(f"✓ Found A2A tool: {tool.name}")
    print(f"  Description: {tool.description}")
    
    # Test the tool execution
    print(f"\n🚀 Executing A2A tool with message: 'show me all pods'")
    
    try:
        result = tool.run()
        print(f"\n✅ A2A Tool Execution Result:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ Error executing A2A tool: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_a2a_execution()
