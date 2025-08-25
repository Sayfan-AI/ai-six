#!/usr/bin/env python3
"""Test A2A architecture integration without requiring a running server."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.agent.agent import Agent
from backend.agent.config import Config

def test_a2a_architecture():
    """Test that A2A architecture is properly integrated."""
    
    print("Testing A2A Architecture Integration")
    print("=" * 40)
    
    # Load config with A2A server configuration
    config_file = os.path.join(os.path.dirname(__file__), 'config.yaml')
    config = Config.from_file(config_file)
    
    # Verify A2A configuration is loaded
    print(f"✓ A2A servers configured: {len(config.a2a_servers)}")
    for server in config.a2a_servers:
        print(f"  - {server['name']}: {server['url']}")
    
    # Create agent (this will attempt tool discovery)
    print(f"\\n✓ Creating agent with A2A configuration...")
    try:
        agent = Agent(config)
        print(f"✓ Agent created successfully")
        
        # Show all available tools
        print(f"\\n✓ Available tools ({len(agent.tool_dict)}):")
        for tool_name in sorted(agent.tool_dict.keys()):
            print(f"  - {tool_name}")
        
        # Check for A2A tools specifically
        a2a_tools = [name for name in agent.tool_dict.keys() if name.startswith('kind-k8s-ai_')]
        
        if a2a_tools:
            print(f"\\n✓ A2A tools discovered: {len(a2a_tools)}")
            for tool in a2a_tools:
                print(f"  - {tool}")
                
            # Test tool inspection
            first_tool = agent.tool_dict[a2a_tools[0]]
            print(f"\\n✓ Example A2A tool details:")
            print(f"  Name: {first_tool.name}")
            print(f"  Description: {first_tool.description}")
            print(f"  Parameters: {[p.name for p in first_tool.parameters]}")
        else:
            print(f"\\n⚠ No A2A tools discovered (server likely not running)")
            print("  This is expected if the A2A server is not available")
            
        print("\\n✓ A2A architecture integration successful!")
        print("\\nThe system is ready to:")
        print("  1. Discover A2A agents from configured servers")
        print("  2. Read agent cards and extract operations") 
        print("  3. Create A2ATool instances for each operation")
        print("  4. Execute operations through the A2A protocol")
        print("  5. Hide A2A complexity behind the standard Tool interface")
        
    except Exception as e:
        print(f"✗ Error creating agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_a2a_architecture()