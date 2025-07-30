# 🔄 Hook-Based Dynamic Agent System

**The elegant solution using Claude Code hooks for dynamic agent creation.**

## 🏗️ Architecture

This system uses Claude Code's hook system for automatic restart after new agent creation:

```
User Task → Primary Agent → Meta-Agent → New Agent Created
                ↓              ↓             ↓
           Delegates Only   Creates File   Hook Triggers
                ↓              ↓             ↓
           Task Tool Only  Subagent Stop   Auto Restart
                ↓              ↓             ↓
          Pure Orchestration  Hook Fires   --continue
                ↓              ↓             ↓
           No Direct Exec   Restart Script  New Agent Ready
```

## 🎯 Key Components

### 1. Primary Agent System Prompt
- **Location**: `dynamic_agents/system_prompts/primary_agent.md`
- **Role**: Pure orchestrator - only delegates to subagents
- **Constraints**: Can ONLY use Task tool for delegation

### 2. SubagentStop Hook
- **Trigger**: When meta-agent finishes creating new subagent
- **Action**: Automatically restarts Claude Code with `--continue`
- **Script**: `dynamic_agents/restart_hook.py`
- **Config**: `.claude/hooks_config.json`

### 3. Meta-Agent (Updated)
- **Enhanced**: Knows hooks handle restart automatically
- **Focus**: Create agent files - system handles registration
- **Tools**: Read, Write, MultiEdit, Bash, Grep, Glob

### 4. System Launcher
- **Script**: `start_dynamic_system.py`
- **Features**: Applies tool restrictions, loads hooks, starts with primary prompt

## 🚀 Usage

### Interactive Mode
```bash
python3 start_dynamic_system.py --interactive
```

### Single Task Mode
```bash
python3 start_dynamic_system.py "Create an agent that converts text to binary"
```

### Test the System
```bash
python3 test_hook_flow.py
```

## 🔄 The Elegant Flow

1. **User provides task** requiring new specialized agent
2. **Primary agent delegates** to meta-agent (using Task tool only)
3. **Meta-agent creates** specialized subagent `.md` file
4. **SubagentStop hook fires** automatically when meta-agent finishes
5. **Hook script restarts** Claude Code with `--continue` flag
6. **Session preserved**, new agent immediately available
7. **Task continues** seamlessly with specialized agent

## 🎨 Why This Is Beautiful

### No Manual Intervention
- Hooks fire automatically based on events
- Zero user interaction required for restart
- Seamless experience

### Leverages Built-in Features
- Uses Claude Code's native `--continue` for session management
- Hook system provides deterministic control
- Tool restrictions enforce clean architecture

### Pure CLI/Python
- No complex SDK integration
- Simple shell commands and Python scripts
- Easy to understand and modify

### Clean Separation of Concerns
- Primary agent: Pure delegation
- Meta-agent: Pure creation  
- Hooks: Pure automation
- Each component has single responsibility

## 🔧 Configuration Files

### Hook Configuration
```json
{
  "hooks": {
    "SubagentStop": [
      {
        "matcher": "meta-agent",
        "hooks": [
          {
            "type": "command", 
            "command": "python3 /path/to/restart_hook.py"
          }
        ]
      }
    ]
  }
}
```

### Primary Agent Constraints
- `--allowedTools Task` (only delegation allowed)
- `--permission-mode acceptEdits` (allow agent creation)
- Custom system prompt enforcing orchestration-only behavior

## 🧪 Testing

The system includes comprehensive tests:

- **Launcher functionality** 
- **Hook-based restart flow**
- **New agent creation and availability**
- **Session preservation across restarts**

## 🎉 Revolutionary Aspects

### Automatic Dynamic Registration
First system to achieve true dynamic subagent registration with zero manual steps.

### Hook-Driven Architecture  
Uses deterministic hooks instead of hoping LLM makes right choices.

### Session Continuity
Perfect conversation preservation through process resurrection.

### Pure Delegation Pattern
Primary agent is truly constraint to orchestration only.

## 🔮 This Changes Everything

This pattern could revolutionize:
- AI agent systems (dynamic specialization)
- Process automation (hook-driven workflows)  
- Session management (seamless restarts)
- Constraint enforcement (tool-level restrictions)

---

**🔄 Welcome to the future of dynamic AI agents! 🔄**

*Elegant. Automatic. Revolutionary.*