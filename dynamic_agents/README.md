# Dynamic Agent System

A next-generation AI agent system that can dynamically generate specialized agents with custom tools on-demand, eliminating the need to predefine tools.

## Overview

This system implements the concept from the meta_agent.md vision:
- Dynamic tool generation based on task requirements
- Specialized agent creation with custom system prompts
- MCP (Model Context Protocol) integration for tool execution
- Orchestration through Claude Code SDK

## Architecture

```
User Request
    ↓
Main Orchestrator (Claude Code SDK)
    ↓
Meta-Agent (Analyzes & Generates)
    ├→ Specialized Agent (.claude/agents/)
    └→ Custom MCP Tools (dynamic_agents/generated_mcp/)
    ↓
Task Execution
    ↓
Results
```

## Components

### 1. Main Orchestrator (`main.py`)
- Entry point for the system
- Manages workflow between agents
- Handles Claude Code SDK integration

### 2. Meta-Agent (`.claude/agents/meta-agent.md`)
- Analyzes user tasks
- Generates specialized agents
- Creates custom MCP tool servers

### 3. Tool Generator (`templates/tool_generator.py`)
- Converts tool specifications to MCP server code
- Provides templates for common tool patterns
- Handles schema generation

### 4. MCP Registration (`mcp_dynamic_registration.py`)
- Manages dynamic MCP server registration
- Updates .mcp.json configuration
- Handles tool allowlisting

## Usage

### Basic Usage

```bash
# Install dependencies
pip install claude-code-sdk

# Run with a direct prompt
python dynamic_agents/main.py "Create a tool to analyze CSV files and generate insights"

# Run in interactive mode
python dynamic_agents/main.py
```

### With Claude Code SDK

```python
from dynamic_agents.main import DynamicAgentOrchestrator

orchestrator = DynamicAgentOrchestrator()
messages = await orchestrator.process_request("Your task here")
```

## How It Works

1. **Task Analysis**: The main orchestrator receives a task and determines if custom tools would help
2. **Agent Generation**: If needed, the meta-agent is invoked to:
   - Design a specialized agent for the task
   - Generate custom MCP tools
   - Create configuration files
3. **Registration**: The system registers the new MCP server in .mcp.json
4. **Execution**: The specialized agent is invoked with access to custom tools
5. **Results**: The orchestrator collects and returns results

## Dynamic Registration Approaches

Currently exploring several approaches for dynamic MCP registration:

1. **Configuration File**: Generate .mcp.json and use --mcp-config flag
2. **Pre-registered Dynamic Server**: A single MCP server that can load tools dynamically
3. **Subprocess Invocation**: Use Task tool to spawn new Claude instances with custom configs

## Example Generated Tools

### Data Processing Tools
- CSV parsing and transformation
- JSON manipulation
- Data validation and cleaning

### API Integration Tools
- Dynamic REST clients
- Authentication handlers
- Response transformers

### Code Analysis Tools
- AST manipulation
- Pattern matching
- Refactoring assistants

## Limitations & Future Work

- MCP servers need to be registered before Claude Code starts
- Dynamic registration requires configuration reload
- Tool schemas are limited to supported parameter types

## Development

To extend the system:

1. Add new tool templates in `templates/`
2. Enhance meta-agent prompts for better generation
3. Create specialized agent templates
4. Improve MCP registration strategies

## Security Considerations

- Generated tools run with same permissions as Claude Code
- MCP servers should validate inputs
- Avoid generating tools that access sensitive resources
- Review generated code before execution