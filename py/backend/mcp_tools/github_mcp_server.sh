#!/bin/bash

# GitHub MCP Server - implements MCP protocol for GitHub CLI tools

# Read JSON-RPC messages from stdin and respond
while read -r line; do
    method=$(echo "$line" | jq -r '.method' 2>/dev/null)
    id=$(echo "$line" | jq -r '.id' 2>/dev/null)
    params=$(echo "$line" | jq -r '.params' 2>/dev/null)
    
    case "$method" in
        "initialize")
            # MCP initialization handshake
            cat << EOF
{"jsonrpc":"2.0","id":$id,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{},"resources":{}},"serverInfo":{"name":"GitHub CLI Tools","version":"1.0.0"}}}
EOF
            ;;
        "notifications/initialized")
            # Notification - no response needed, just acknowledge
            ;;
        "tools/list")  
            # Return available GitHub tools
            cat << EOF
{"jsonrpc":"2.0","id":$id,"result":{"tools":[{"name":"gh","description":"Execute GitHub CLI commands","inputSchema":{"type":"object","properties":{"args":{"type":"string","description":"GitHub CLI command arguments"}},"required":["args"]}}]}}
EOF
            ;;
        "tools/call")
            # Handle tool invocation
            tool_name=$(echo "$params" | jq -r '.name' 2>/dev/null)
            args=$(echo "$params" | jq -r '.arguments.args' 2>/dev/null)
            
            if [ "$tool_name" = "gh" ]; then
                # Execute gh command and capture output
                result=$(gh $args 2>&1)
                exit_code=$?
                
                if [ $exit_code -eq 0 ]; then
                    # Success - escape JSON and return result
                    escaped_result=$(echo "$result" | jq -Rs .)
                    cat << EOF
{"jsonrpc":"2.0","id":$id,"result":{"content":[{"type":"text","text":$escaped_result}]}}
EOF
                else
                    # Error - return the error as content so LLM can see and adjust
                    escaped_error=$(echo "$result" | jq -Rs .)
                    cat << EOF
{"jsonrpc":"2.0","id":$id,"result":{"content":[{"type":"text","text":$escaped_error}]}}
EOF
                fi
            else
                # Unknown tool
                cat << EOF
{"jsonrpc":"2.0","id":$id,"error":{"code":-32602,"message":"Unknown tool: $tool_name"}}
EOF
            fi
            ;;
        *)
            # Unknown method - only send error for requests (with id), not notifications
            if [ "$id" != "null" ]; then
                cat << EOF
{"jsonrpc":"2.0","id":$id,"error":{"code":-32601,"message":"Method not found: $method"}}
EOF
            fi
            ;;
    esac
    
done
