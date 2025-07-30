# Dynamic Agent System - Solution Approach

## The Challenge

A running Claude Code instance cannot use subagents or MCP tools that are created AFTER it was invoked because:
- Subagents are loaded from `.claude/agents/` at startup
- MCP servers are loaded from configuration at startup
- No hot-reload mechanism exists

## Recommended Solution: Dynamic Tool Loader

### Architecture

```
┌─────────────────────────┐
│   Claude Code Instance  │
│  (Started with loader)  │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Dynamic Tool Loader    │ ← Pre-registered MCP server
│    (MCP Server)         │   that can load tools dynamically
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  generated_tools/       │ ← Tool definitions added at runtime
│  - tool1.json          │
│  - tool2.json          │
└─────────────────────────┘
```

### Implementation Steps

1. **Pre-register the dynamic loader** in `.mcp.json`:
```json
{
  "mcpServers": {
    "dynamic-tools": {
      "command": "node",
      "args": ["./dynamic_agents/dynamic_tool_loader.js"]
    }
  }
}
```

2. **Meta-agent generates tool definitions** as JSON files in `generated_tools/`

3. **Dynamic loader serves these tools** without restart

4. **Tools are accessed as**: `mcp__dynamic-tools__toolname`

### Advantages
- No Claude Code restart needed
- Tools available immediately after generation
- Single point of dynamic tool management
- Clean separation of concerns

### Alternative Approaches

#### 1. Task Tool Chaining
- Meta-agent creates resources
- Generated agent uses Task tool to spawn fresh instance
- New instance has access to everything
- **Pro**: Works today without changes
- **Con**: Creates nested instances

#### 2. SDK Orchestration
- Python controls lifecycle
- Phase 1: Generate resources
- Phase 2: Re-invoke with new config
- **Pro**: Full control over flow
- **Con**: More complex orchestration

### Recommended Next Steps

1. Implement the dynamic tool loader
2. Update meta-agent to generate tool JSON files
3. Test with simple tool generation scenarios
4. Iterate on tool definition format