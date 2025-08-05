# Dynamic Agent Creation with Claude Code

An experimental system that demonstrates agents creating their own specialists on demand using Claude Code's hooks, subagents, and MCP integration.

## What This Demonstrates

This proof-of-concept shows how to build agents that can:
- **Create new specialists** when they encounter tasks they can't handle
- **Automatically restart** to register new capabilities (the "Phoenix Pattern")
- **Maintain conversation context** across system restarts
- **Accumulate expertise** over time through specialist creation

## Quick Start: See It In Action

### 1. Run the Calculator Example

**Interactive Mode:**
```bash
python start_dynamic_system.py "create a calculator and calculate 7365464 * 5434536"
```

**Headless Mode (automation-friendly):**
```bash
python start_dynamic_system.py --headless --exit-after-completion "create a calculator and calculate 7365464 * 5434536"
```

**What happens:**
1. Primary agent realizes it needs a calculator specialist
2. Meta-agent creates both calculator agent (.claude/agents/calculator.md) and MCP server (dynamic_agents/generated_mcp/calculator_server.py)
3. System automatically restarts (Phoenix Pattern - preserves context)
4. New calculator specialist uses `mcp__calculator__calculate` tool
5. You get the result: **40,027,879,264,704**

### 2. Try Text Analysis

```bash
python start_dynamic_system.py "Create a word counter specialist that analyzes text files and gives detailed statistics, then use it to analyze README.md"
```

**What happens:**
1. Primary agent realizes it needs a text analysis specialist
2. Meta-agent creates a custom `word-counter` agent 
3. System automatically restarts (Phoenix Pattern)
4. New specialist analyzes your README.md file
5. You get detailed text statistics

### 3. Verify the Magic

Check that a new agent was created:
```bash
ls .claude/agents/
# You'll see: meta-agent.md, word-counter.md (newly created!)
```

Check the logs to see the Phoenix Pattern in action:
```bash
ls logs/
# Shows session directories with restart tracking
```

### 4. Try Another Example

```bash
python start_dynamic_system.py "Create a JSON beautifier specialist and use it to format all JSON files in this directory"
```

The system will create a `json-formatter` specialist and use it immediately.

## How It Works (The Phoenix Pattern)

### The Problem
Claude Code only scans for subagents at startup. Create new ones during a session? They're invisible until restart.

### The Solution
Turn the constraint into a feature:

1. **Meta-agent creates specialist** and completes its subagent task
2. **SubagentStop hook** detects meta-agent completion and triggers restart
3. **System restarts with `--continue "meta-agent finished. continue with original task"`** (preserves context)
4. **New specialist is now available** for the original task

```
User Request → Gap Detection → Meta-Agent → Agent Creation
                                                ↓
Results ← Specialist Execution ← System Restart ← Hook Trigger
```

## Architecture

### Three-Tier Specialization
```
┌─────────────┐
│ User Task   │  
└─────┬───────┘
      ▼
┌──────────────────────┐
│ Primary Agent        │  ← Orchestration only
│ (delegation only)    │  ← No direct execution
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│ Meta-Agent           │  ← Creates specialists
│ (agent factory)      │  ← Generates .md + MCP servers
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│ Specialized Agent(s) │  ← Domain experts
│ (purpose-built)      │  ← Minimal permissions
└──────────────────────┘
```

### Key Files

- **`start_dynamic_system.py`** - Main launcher script
- **`.claude/agents/meta-agent.md`** - The agent factory
- **`.claude/hooks/subagent_stop.py`** - Phoenix Pattern trigger
- **`.claude/settings.json`** - Hook configuration

## Real Session Example

The system creates session logs that track the complete Phoenix Pattern execution. You can see the actual session events in `session_events.json` after running the system.

## Advanced Usage

### Interactive Mode
```bash
python start_dynamic_system.py --interactive
```

### Headless Mode (for automation)
```bash
# Suppress UI output, show only results
python start_dynamic_system.py --headless "your task here"

# Exit automatically after completion (great for scripts)
python start_dynamic_system.py --headless --exit-after-completion "your task here"
```

### Check System Status
```bash
# See created specialists
cat .claude/agents/*.md

```

### Create Specific Specialists
```bash
# Code analysis specialist
python start_dynamic_system.py "Create a Python code reviewer that checks for best practices and suggests improvements"

# Data processing specialist  
python start_dynamic_system.py "Create a CSV analyzer that generates statistical summaries and visualizations"

# Log analysis specialist
python start_dynamic_system.py "Create a log file parser that extracts errors and generates reports"
```

## Setup Instructions

### Prerequisites

1. **Claude Code CLI** - Install from [official docs](https://docs.anthropic.com/en/docs/claude-code)
2. **Python 3.8+**
3. **Git** for cloning the repository

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd dynamic-agent-creation

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# Alternative: if you have uv (faster package manager)
uv pip install -r requirements.txt

# 4. Verify Claude Code is installed
claude --version
```

### Configuration

The system comes pre-configured with all necessary hooks and settings in `.claude/`. No additional setup required!

Key configuration files:
- `.claude/settings.json` - Hook configuration
- `.claude/agents/meta-agent.md` - The agent factory
- `.claude/hooks/subagent_stop.py` - Phoenix Pattern trigger

