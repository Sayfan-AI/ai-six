# A2A Integration Test

This example demonstrates AI-6's A2A (Agent-to-Agent) client support integration.

## Architecture

The A2A integration follows the same pattern as MCP integration:

1. **A2A Client** (`backend/a2a_client/`) - Handles A2A protocol communication
2. **A2ATool** (`backend/tools/base/a2a_tool.py`) - Wraps A2A operations as standard Tools  
3. **Configuration** - A2A servers defined in config under `a2a_servers`
4. **Discovery** - Agent cards fetched at init time, operations become tools

## Key Features

- **Agent Card Discovery**: Automatically fetches `.well-known/agent.json`
- **Operation Mapping**: Each A2A agent operation becomes an individual tool
- **Protocol Abstraction**: A2A tasks/messages/artifacts hidden behind Tool interface
- **Configuration Driven**: A2A servers defined declaratively in config
- **Graceful Degradation**: Works without A2A dependencies, just logs warnings

## Dependencies

For full A2A functionality, install the a2a-client:

```bash
pip install a2a-client
```

## Testing

### Architecture Test (No Server Required)
```bash
python test_architecture.py
```

Tests the integration architecture and tool discovery process.

### Full Integration Test (Requires Server)  
```bash
python test_a2a.py
```

Attempts to start the k8s-ai A2A server and test actual tool execution.

## Configuration

See `config.yaml` for example A2A server configuration:

```yaml
a2a_servers:
  - name: kind-k8s-ai
    url: http://localhost:9999
    timeout: 30.0
enabled_tools:
  - kind-k8s-ai_get_pods
  - kind-k8s-ai_describe_pod
```

## k8s-ai Test Server

The test uses the k8s-ai server from the sibling directory as a test A2A agent.

To run it manually:
```bash
cd ~/git/k8s-ai
python -m k8s_ai.server.main --context kind-kind
```

This requires:
1. The a2a library installed
2. A Kubernetes context named "kind-kind" 
3. kubectl configured and working