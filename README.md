# Dynamic Agent Creation with Claude Code

An experimental system that demonstrates agents creating their own specialists on demand using Claude Code's hooks, subagents, and MCP integration.

## What This Demonstrates

This proof-of-concept shows how to build agents that can:
- **Create new specialists** when they encounter tasks they can't handle
- **Automatically restart** to register new capabilities (the "Phoenix Pattern")
- **Maintain conversation context** across system restarts
- **Accumulate expertise** over time through specialist creation

## Quick Start: See It In Action

### 1. Run the Experiment

```bash
python start_dynamic_system.py "Create a word counter specialist that analyzes text files and gives detailed statistics, then use it to analyze README.md"
```

**What happens:**
1. Primary agent realizes it needs a text analysis specialist
2. Meta-agent creates a custom `word-counter` agent 
3. System automatically restarts (Phoenix Pattern)
4. New specialist analyzes your README.md file
5. You get detailed text statistics

### 2. Verify the Magic

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

### 3. Try Another Example

```bash
python start_dynamic_system.py "Create a JSON beautifier specialist and use it to format all JSON files in this directory"
```

The system will create a `json-formatter` specialist and use it immediately.

## How It Works (The Phoenix Pattern)

### The Problem
Claude Code only scans for subagents at startup. Create new ones during a session? They're invisible until restart.

### The Solution
Turn the constraint into a feature:

1. **Meta-agent creates specialist** and says "**Agent created**"
2. **Hook detects the phrase** and triggers automatic restart
3. **System restarts with `--continue`** (preserves conversation)
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
│ (agent factory)      │  ← Generates .md files
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
- **`.claude/settings.local.json`** - Hook configuration
- **`logs/`** - Session tracking and restart verification

## Real Session Example

From actual logs of creating a JSON formatter:

```json
{
  "event_type": "subagent_stop",
  "subagent_type": "meta-agent",
  "result_preview": "✅ **Agent created**: json-formatter specialized for formatting...",
  "agent_creation_detected": true
}
```

→ Hook triggers restart →

```json
{
  "meta": {
    "status": "restart_triggered",
    "creations": 1
  },
  "metrics": {
    "agents_created": 1,
    "restarts": 1
  }
}
```

## Advanced Usage

### Interactive Mode
```bash
python start_dynamic_system.py --interactive
```

### Check System Status
```bash
# See created specialists
cat .claude/agents/*.md

# Check recent sessions  
ls -la logs/session_*/

# View session details
python -m json.tool logs/session_*/session_metadata.json
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

### Verify Installation

Test the system works:
```bash
python start_dynamic_system.py "Create a simple test agent and use it to say hello"
```

If successful, you'll see:
1. Agent creation in progress
2. Automatic system restart
3. New agent executing the task

### Troubleshooting

**"No module named 'mcp'" error:**
```bash
pip install --upgrade mcp>=1.3.2
```

**Claude Code not found:**
- Install Claude Code CLI from [official documentation](https://docs.anthropic.com/en/docs/claude-code)
- Ensure it's in your PATH: `which claude`

**Hook not triggering restart:**
- Check `.claude/settings.json` exists and has proper hook configuration
- Verify hook permissions: `chmod +x .claude/hooks/subagent_stop.py`
- Check logs in `logs/` directory for error messages

**System requirements:**
- Python 3.8+ (check with `python --version`)
- At least 1GB free disk space
- Internet connection for Claude Code API calls

## What Makes This Interesting

This isn't just dynamic tool use - it's **dynamic capability expansion**. The system doesn't just get better at using existing tools; it creates entirely new capabilities and maintains awareness of what it built.

Each specialist becomes a permanent part of the system, creating compound growth in capabilities over time.

## Limitations

- **2-3 second restart delay** during expansion
- **Requires hook scripts** (though they're simple)
- **30-60 seconds** to create each specialist
- **Single session scope** currently

## The Bigger Picture

This experiment explores what happens when agents can expand their own toolset rather than just use existing tools more cleverly. It demonstrates that constraints in current platforms can become architectural advantages with creative approaches.

The Phoenix Pattern specifically shows how to work with platform limitations rather than against them, turning a registration constraint into a clean separation between capability creation and execution phases.

---

**Try the experiment** and watch your agent system grow new capabilities in real-time.