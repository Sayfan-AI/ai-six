#!/usr/bin/env python3
"""Test script for A2A integration with AI-6."""

import sys
import os
import subprocess
import time
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.agent.agent import Agent
from backend.agent.config import Config

def check_a2a_server():
    """Check if A2A server is running and start it if needed."""
    try:
        response = requests.get('http://localhost:9999/.well-known/agent.json', timeout=5)
        if response.status_code == 200:
            print("A2A server is already running")
            return True
    except:
        pass
    
    print("Starting k8s-ai A2A server...")
    k8s_ai_path = os.path.expanduser('~/git/k8s-ai')
    if not os.path.exists(k8s_ai_path):
        print(f"Error: k8s-ai directory not found at {k8s_ai_path}")
        return False
    
    try:
        # Start the server in the background with kind context
        cmd = ['python', '-m', 'k8s_ai.server.main', '--context', 'kind-kind']
        subprocess.Popen(cmd, cwd=k8s_ai_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for server to start
        for i in range(10):
            try:
                response = requests.get('http://localhost:9999/.well-known/agent.json', timeout=2)
                if response.status_code == 200:
                    print("A2A server started successfully")
                    return True
            except:
                pass
            time.sleep(1)
        
        print("Failed to start A2A server")
        return False
        
    except Exception as e:
        print(f"Error starting A2A server: {e}")
        return False

def test_a2a_integration():
    """Test A2A tool discovery and execution."""
    
    # Check/start A2A server (optional - test will work without it)
    server_running = check_a2a_server()
    if not server_running:
        print("Note: A2A server not available, testing tool discovery only\\n")
    
    # Load config with A2A server configuration
    config_file = os.path.join(os.path.dirname(__file__), 'config.yaml')
    config = Config.from_file(config_file)
    
    # Create agent
    agent = Agent(config)
    
    print("\nAvailable tools:")
    for tool_name in agent.tool_dict.keys():
        print(f"  - {tool_name}")
    
    # Test A2A tool execution
    a2a_tools = [name for name in agent.tool_dict.keys() if name.startswith('kind-k8s-ai_')]
    
    if a2a_tools:
        print(f"\nFound A2A tools: {a2a_tools}")
        
        # Try to use the first A2A tool
        first_tool = a2a_tools[0]
        print(f"\nTesting {first_tool}:")
        
        try:
            result = agent.tool_dict[first_tool].run()
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error executing {first_tool}: {e}")
    else:
        print("\nNo A2A tools found. Check that:")
        print("1. The k8s-ai A2A server is running on http://localhost:9999")
        print("2. The a2a-client library is installed")
        print("3. The server configuration is correct")

if __name__ == "__main__":
    test_a2a_integration()