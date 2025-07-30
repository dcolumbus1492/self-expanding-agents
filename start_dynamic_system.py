#!/usr/bin/env python3
"""
Dynamic Agent System Launcher
Starts Claude Code with primary agent configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_configuration():
    """Set up the configuration for dynamic agent system"""
    
    # Read primary agent system prompt
    system_prompt_file = Path("dynamic_agents/system_prompts/primary_agent.md")
    if not system_prompt_file.exists():
        print("❌ Primary agent system prompt not found!")
        return False
    
    primary_prompt = system_prompt_file.read_text()
    
    print("✅ Primary agent system prompt loaded")
    return primary_prompt

def start_claude_with_config(system_prompt, task=None):
    """Start Claude Code with primary agent configuration"""
    
    # Build Claude command with restrictions
    cmd = [
        "claude",
        "--system-prompt", system_prompt,
        "--allowedTools", "Task",  # Only allow Task tool for delegation
        "--permission-mode", "acceptEdits"  # Accept edits to create subagents
    ]
    
    # Add task if provided
    if task:
        cmd.extend(["-p", task])
    
    print("🚀 Starting dynamic agent system...")
    print(f"🎯 Allowed tools: Task only")
    print(f"🔧 Hooks: SubagentStop → restart")
    
    if task:
        print(f"📋 Task: {task}")
    else:
        print("🔄 Interactive mode")
    
    # Execute Claude Code
    try:
        result = subprocess.run(cmd, cwd=os.getcwd())
        return result.returncode
    except KeyboardInterrupt:
        print("\n👋 Dynamic agent system stopped")
        return 0
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        return 1

def main():
    """Main launcher"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🔄 Dynamic Agent System")
    parser.add_argument("task", nargs="?", help="Task to execute")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    print("🔄 DYNAMIC AGENT SYSTEM LAUNCHER")
    print("=" * 50)
    
    # Setup configuration
    system_prompt = setup_configuration()
    if not system_prompt:
        sys.exit(1)
    
    # Start Claude Code
    if args.task:
        # Single task mode
        return_code = start_claude_with_config(system_prompt, args.task)
    elif args.interactive:
        # Interactive mode
        return_code = start_claude_with_config(system_prompt, None)  
    else:
        # Default: show help
        parser.print_help()
        return_code = 0
    
    sys.exit(return_code)

if __name__ == "__main__":
    main()