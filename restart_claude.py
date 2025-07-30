#!/usr/bin/env python3
"""
Simple restart script for Claude Code to reload MCP configuration
"""

import os
import sys
import subprocess

def restart_claude_code():
    """Restart Claude Code with --continue flag to preserve session"""
    print("Restarting Claude Code with updated MCP configuration...")
    
    # Get current working directory
    cwd = os.getcwd()
    
    # Prepare command
    cmd = [
        "claude-code",
        "--continue",
        "--allowedTools", 
        "Read,Write,MultiEdit,Bash,Grep,Glob,mcp__leetspeak_server__convert_to_basic_leet,mcp__leetspeak_server__convert_to_advanced_leet,mcp__leetspeak_server__convert_to_elite_leet,mcp__leetspeak_server__convert_from_basic_leet,mcp__leetspeak_server__convert_from_advanced_leet,mcp__leetspeak_server__convert_from_elite_leet,mcp__leetspeak_server__convert_file_to_leet,mcp__leetspeak_server__convert_file_from_leet,mcp__leetspeak_server__create_custom_mapping"
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    print(f"Working directory: {cwd}")
    
    # Execute restart
    try:
        os.execvp("claude-code", cmd[0:])
    except Exception as e:
        print(f"Error restarting Claude Code: {e}")
        sys.exit(1)

if __name__ == "__main__":
    restart_claude_code()