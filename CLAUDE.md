# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a dynamic agent system that implements the concept of next-generation AI agents with dynamic tool generation capabilities. The system can generate specialized agents with custom MCP (Model Context Protocol) tools on-demand, eliminating the need to predefine tools.

## Environment

**This is a macOS machine. All CLI commands should be shell/bash commands unless otherwise specified.**

## Core Commands

### Setting up the environment
```bash
# Create virtual environment with uv
uv venv

# Activate virtual environment (macOS/Linux)
source .venv/bin/activate

# Install dependencies
uv pip install claude-code-sdk
```

### Running the Dynamic Agent System
```bash
# Run with a direct prompt
python dynamic_agents/main.py "Your task here"

# Run in interactive mode
python dynamic_agents/main.py

# Run with verbose logging
python dynamic_agents/main.py --verbose "Your task"
```

### Testing and Development
Since no test framework is currently set up, when implementing features:
1. Test manually by running the system with various prompts
2. Check logs with `--verbose` flag
3. Verify generated files in `.claude/agents/` and `dynamic_agents/generated_mcp/`

## Architecture

### Key Components

1. **Main Orchestrator** (`dynamic_agents/main.py`)
   - Entry point that uses Claude Code SDK
   - Manages workflow between user, meta-agent, and specialized agents
   - Handles async execution and message streaming

2. **Meta-Agent** (`.claude/agents/meta-agent.md`)
   - Analyzes tasks to determine if custom tools would help
   - Generates specialized agents with system prompts
   - Creates MCP tool servers when needed

3. **System Prompts** (`dynamic_agents/system_prompts/`)
   - Contains workflow prompts that guide agent behavior
   - Main orchestrator prompt defines coordination logic

4. **MCP Integration** (`dynamic_agents/mcp_dynamic_registration.py`)
   - Handles dynamic registration of MCP servers
   - Updates `.mcp.json` configuration
   - Manages tool allowlisting

### Workflow

1. User request → Main Orchestrator
2. Orchestrator analyzes if custom tools needed → Invokes Meta-Agent
3. Meta-Agent generates specialized agent + MCP tools
4. System registers MCP server and invokes specialized agent
5. Results returned to user

## Important Patterns

### Agent Definition Format
```markdown
---
name: agent-name
description: When to use this agent
tools: Tool1, Tool2, mcp__server__tool
---

[System prompt content]
```

### MCP Tool Naming
- MCP tools follow pattern: `mcp__<serverName>__<toolName>`
- Server names from `.mcp.json` configuration
- Must be explicitly allowed via `--allowedTools`

### macOS-Specific Considerations
- All CLI commands are bash/shell unless otherwise specified
- Node.js commands can be run directly without cmd wrapper
- File paths must be absolute, not relative
- Git commands work natively
- Virtual environment activation: `source .venv/bin/activate`

## Key Directories

- `.claude/agents/` - Generated specialized agents
- `dynamic_agents/generated_mcp/` - Generated MCP tool servers  
- `dynamic_agents/system_prompts/` - System prompt templates
- `dynamic_agents/templates/` - Tool generation templates

## Current Limitations

1. MCP servers must be registered before Claude Code starts
2. Dynamic registration requires configuration reload
3. No automated test framework currently set up
4. Tool schemas limited to supported parameter types

## Development Guidelines

When extending the system:
1. Follow existing patterns in `main.py` for orchestration logic
2. Use the meta-agent for generating new specialized agents
3. Create MCP tools as single-purpose, focused functions
4. Test with various prompts to ensure robustness
5. Add logging for debugging complex workflows