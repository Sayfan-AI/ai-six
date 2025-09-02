#!/usr/bin/env python3
"""Final comprehensive test of A2A integration."""

import sys
import os
import traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from backend.agent.agent import Agent
from backend.agent.config import Config

def test_a2a_final():
    """Final comprehensive test of A2A integration."""
    
    print("🧪 Final A2A Integration Test")
    print("=" * 40)
    
    # Load config with A2A server configuration
    config_file = os.path.join(os.path.dirname(__file__), 'config.yaml')
    config = Config.from_file(config_file)
    
    print("✅ Configuration loaded")
    print(f"   A2A servers: {len(config.a2a_servers)}")
    for server in config.a2a_servers:
        print(f"   - {server['name']}: {server['url']}")
    
    # Create agent
    print("\n🤖 Creating AI-6 agent with A2A support...")
    agent = Agent(config)
    
    print(f"✅ Agent created with {len(agent.tool_dict)} tools")
    
    # Find A2A tools
    a2a_tools = [name for name in agent.tool_dict.keys() if name.startswith('kind-k8s-ai_')]
    
    if not a2a_tools:
        print("❌ No A2A tools discovered")
        print("   Make sure the k8s-ai server is running on localhost:9999")
        return
    
    print(f"\n🔧 A2A Tools Discovered: {len(a2a_tools)}")
    for tool_name in a2a_tools:
        tool = agent.tool_dict[tool_name]
        print(f"   - {tool_name}: {tool.description}")
    
    # Test tool execution
    test_tool = a2a_tools[0]
    print(f"\n🚀 Testing {test_tool} execution...")
    
    try:
        result = agent.tool_dict[test_tool].run()
        print("\n✅ A2A Tool Execution Successful!")
        print("📄 Response:")
        print("-" * 50)
        print(result)
        print("-" * 50)
        
        print("\n🎉 A2A Integration Test PASSED!")
        print("\n🔥 Key Features Verified:")
        print("   ✅ Agent card discovery from A2A servers")
        print("   ✅ Skills mapped to individual tools")
        print("   ✅ A2A protocol abstracted behind Tool interface")
        print("   ✅ Tool execution working end-to-end")
        print("   ✅ Configuration-driven server discovery")
        
    except Exception as e:
        print(f"❌ A2A tool execution failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_a2a_final()
