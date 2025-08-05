# Simple MCP Server Guide for Dynamic Agents

This guide provides a streamlined approach to creating simple, stdio-based MCP servers.

## Core Principles

1. **Simple stdio protocol** - No complex frameworks or dependencies
2. **Direct JSON communication** - Raw stdin/stdout with JSON-RPC
3. **Auto-registration compatible** - Works with `claude mcp add` command
4. **Minimal viable implementation** - Only what's needed for the task

## MCP Server Template

```python
#!/usr/bin/env python3

import asyncio
import json
import sys
from typing import Any, Dict

class SimpleMCPServer:
    def __init__(self):
        self.tools = {
            "tool_name": {
                "name": "tool_name",
                "description": "What this tool does",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "param": {"type": "string", "description": "Parameter description"}
                    },
                    "required": ["param"]
                }
            }
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "server-name",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0", 
                "id": request.get("id"),
                "result": {"tools": list(self.tools.values())}
            }
        
        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            try:
                result = await self.execute_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [{"type": "text", "text": str(result)}]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32000, "message": str(e)}
                }

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]):
        if tool_name == "tool_name":
            # Implement your tool logic here
            return f"Result: {arguments.get('param', '')}"
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def run(self):
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line.strip())
                response = await self.handle_request(request)
                print(json.dumps(response), flush=True)
            except (EOFError, KeyboardInterrupt, json.JSONDecodeError):
                break

if __name__ == "__main__":
    server = SimpleMCPServer()
    asyncio.run(server.run())
```

## Implementation Steps

### 1. Define Your Tools
```python
self.tools = {
    "action_name": {
        "name": "action_name", 
        "description": "Description of what this action does",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input1": {"type": "string", "description": "First input parameter"},
                "input2": {"type": "number", "description": "Second input parameter"}
            },
            "required": ["input1", "input2"]
        }
    }
}
```

### 2. Implement Tool Logic
```python
async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]):
    if tool_name == "action_name":
        # Your implementation here
        return process_inputs(arguments["input1"], arguments["input2"])
    else:
        raise ValueError(f"Unknown tool: {tool_name}")
```

### 3. Update Server Info
```python
"serverInfo": {
    "name": "your-server-name",  # Used in mcp__server-name__tool pattern
    "version": "1.0.0"
}
```

## File Naming Convention

- **File name**: `{purpose}_server.py` (e.g., `text_processor_server.py`)
- **Server name**: Derived from filename with underscores converted to hyphens
- **Location**: `dynamic_agents/generated_mcp/`

## Registration Process

1. **Create server** in `dynamic_agents/generated_mcp/`
2. **Register with Claude Code**: `claude mcp add server-name -- python /full/path/server.py`
3. **Tools available** as `mcp__server-name__tool-name`

## Error Handling

```python
try:
    # Tool execution logic
    result = perform_operation(arguments)
    return result
except ValueError as e:
    raise ValueError(f"Invalid input: {e}")
except Exception as e:
    raise ValueError(f"Operation failed: {e}")
```

## Testing Your Server

```python
# Simple test script
import json
import subprocess
import sys

def test_server():
    process = subprocess.Popen(
        [sys.executable, "your_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    
    # Test initialize
    init_request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    process.stdin.write(json.dumps(init_request) + "\n")
    process.stdin.flush()
    response = json.loads(process.stdout.readline())
    print("Server initialized:", response["result"]["serverInfo"]["name"])
    
    process.terminate()

if __name__ == "__main__":
    test_server()
```

## Best Practices

### DO:
- ✅ Use simple JSON-RPC over stdio
- ✅ Handle all three required methods: `initialize`, `tools/list`, `tools/call`
- ✅ Provide clear tool descriptions and schemas
- ✅ Include proper error handling
- ✅ Use meaningful tool and parameter names
- ✅ Make servers executable: `chmod +x server.py`

### DON'T:
- ❌ Use complex MCP frameworks or libraries
- ❌ Add unnecessary dependencies
- ❌ Create tools that aren't specifically needed
- ❌ Forget to handle initialization properly
- ❌ Use complex async patterns beyond basic asyncio.run()

## Common Patterns

### Data Processing
```python
async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]):
    if tool_name == "process":
        data = arguments["data"]
        operation = arguments["operation"]
        
        if operation == "transform": return transform_data(data)
        elif operation == "filter": return filter_data(data)
        else: raise ValueError(f"Unknown operation: {operation}")
```

### Text Operations
```python
async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]):
    if tool_name == "text_operation":
        text = arguments["text"]
        operation = arguments["operation"]
        
        if operation == "format": return format_text(text)
        elif operation == "analyze": return analyze_text(text)
        else: raise ValueError(f"Unknown operation: {operation}")
```

### Validation
```python
async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]):
    if tool_name == "validate":
        value = arguments["value"]
        rule = arguments["rule"]
        
        return validate_by_rule(value, rule)
```

This approach ensures your MCP servers are simple, reliable, and compatible with Claude Code.