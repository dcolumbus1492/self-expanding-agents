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
    
    # CRITICAL: Create concise system prompt to avoid command line length issues
    enhanced_prompt = system_prompt + """

🚨 CRITICAL: You can ONLY use the Task tool. All other tools are FORBIDDEN.

If you attempt any non-Task tool, respond: "TOOL_VIOLATION: [toolname] - Task delegation required" and delegate to meta-agent via Task tool.
"""
    
    # Create temporary system prompt file to avoid command line length issues
    import tempfile
    prompt_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
    prompt_file.write(enhanced_prompt)
    prompt_file.flush()
    prompt_file.close()
    
    # Build Claude command - ENFORCED tool restriction for primary agent
    # PRIMARY AGENT: Only Task tool allowed (enforced by Claude Code flags)
    # SUBAGENTS: Full tool access (flags don't affect subagents)
    cmd = [
        "claude",
        "--system-prompt-file", prompt_file.name,
        "--permission-mode", "acceptEdits",  # Accept edits to create subagents
        "--allowedTools", "Task"  # CRITICAL: Restrict primary agent to Task only
    ]
    
    # DUAL ENFORCEMENT: System prompt + Claude Code flags
    # Primary agent: Restricted to Task tool only (via --allowedTools)
    # Subagents: Full tool access (tool restrictions don't cascade to subagents)
    print("🔒 DUAL TOOL RESTRICTIONS ACTIVE:")
    print("   1. PRIMARY AGENT: Task tool only (--allowedTools Task)")
    print("   2. SUBAGENTS: Full tool access (restrictions don't cascade)")
    print("   3. Meta-agent: Can use Write tools to create files")
    print("🔄 All operations MUST be delegated via Task tool")
    
    # Add task handling
    if task:
        print(f"📝 Task will be provided via stdin: {task}")
    
    print("🚀 Starting dynamic agent system...")
    print(f"🎯 Primary agent: Task tool only")
    print(f"🔧 Hooks: Phoenix Pattern → deterministic restart")
    
    if task:
        print(f"📋 Task: {task}")
    else:
        print("🔄 Interactive mode")
    
    print(f"🔧 Command: claude --system-prompt-file [TEMP_FILE] --permission-mode acceptEdits")
    
    # Execute Claude Code
    try:
        if task:
            # Write task to temp file and use -p to avoid interactive mode
            task_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            task_file.write(task)
            task_file.flush()
            task_file.close()
            
            cmd.extend(["-p", f"@{task_file.name}"])
            result = subprocess.run(cmd, cwd=os.getcwd())
            
            # Check if Phoenix restart occurred
            restart_file = Path("PHOENIX_RESTART_EXECUTED.txt")
            if restart_file.exists():
                print("🔄 Phoenix restart detected - continuing with new agent...")
                
                # Wait for restart to complete
                import time
                time.sleep(3)
                
                # Continue with the original task using new agent
                continue_cmd = [
                    "claude",
                    "--continue",
                    "-p", task
                ]
                print("🚀 Continuing with new specialized agent...")
                result = subprocess.run(continue_cmd, cwd=os.getcwd())
            
            # Clean up
            try:
                os.unlink(task_file.name)
            except:
                pass
                
            return result.returncode
        else:
            # Direct interactive mode
            result = subprocess.run(cmd, cwd=os.getcwd())
            return result.returncode
    except KeyboardInterrupt:
        print("\n👋 Dynamic agent system stopped")
        return 0
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        return 1
    finally:
        # Clean up temporary file
        try:
            os.unlink(prompt_file.name)
        except:
            pass

def main():
    """Main launcher"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🔄 Dynamic Agent System")
    parser.add_argument("task", nargs="?", help="Task to execute")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--test-prompt", help="Test prompt for validation")
    
    args = parser.parse_args()
    
    print("🔄 DYNAMIC AGENT SYSTEM LAUNCHER")
    print("=" * 50)
    
    # Setup configuration
    system_prompt = setup_configuration()
    if not system_prompt:
        sys.exit(1)
    
    # Start Claude Code
    if args.test_prompt:
        # Test prompt mode for validation
        print("🧪 TEST MODE: Using test prompt")
        return_code = start_claude_with_config(system_prompt, args.test_prompt)
    elif args.task:
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