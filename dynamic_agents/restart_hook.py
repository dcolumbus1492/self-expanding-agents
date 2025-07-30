#!/usr/bin/env python3
"""
Dynamic Agent Restart Hook
Triggers when meta-agent finishes creating new subagent
"""

import json
import sys
import os
import subprocess
import tempfile
from pathlib import Path

def main():
    """Hook script for restarting after meta-agent creates subagent"""
    
    try:
        # Read hook data from stdin
        try:
            hook_data = json.load(sys.stdin)
        except json.JSONDecodeError:
            # If no JSON data, read raw input
            raw_input = sys.stdin.read()
            print(f"Hook received raw input: {raw_input}", file=sys.stderr)
            hook_data = {}
        
        print(f"Hook received data: {json.dumps(hook_data, indent=2)}", file=sys.stderr)
        
        # Check if this was a meta-agent subagent task
        subagent_type = hook_data.get('subagent_type', '')
        task_result = hook_data.get('result', str(hook_data))
        
        # For SubagentStop hook, we should check if it's for meta-agent
        # The hook is already filtered by matcher, so if we get here it's meta-agent
        print("🔄 SubagentStop hook triggered for meta-agent", file=sys.stderr)
        
        # Check if new agent was likely created
        # Look for indicators in the result or assume meta-agent created something
        likely_created = (
            any(keyword in task_result.lower() for keyword in [
                'agent created', 'generated', 'specialized agent', 'subagent', 'created'
            ]) or 
            len(task_result) > 50  # Assume substantial output means agent was created
        )
        
        if likely_created:
            # Get current session info
            session_id = hook_data.get('session_id', '')
            working_dir = os.getcwd()
            
            print("🔄 Meta-agent finished - new subagent created!")
            print("🔄 Triggering restart to load new agent...")
            
            # Create restart script
            restart_script = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.sh',
                prefix='dynamic_restart_',
                delete=False
            )
            
            restart_script.write(f'''#!/bin/bash
# Dynamic Agent Restart Script
echo "🔄 Restarting Claude Code to load new subagent..."

# Wait for current process to exit
sleep 2

# Change to working directory
cd "{working_dir}"

# Restart Claude Code with continuation
claude --continue

echo "✅ Claude Code restarted with new subagent available!"

# Clean up
rm -f "{restart_script.name}"
''')
            
            restart_script.flush()
            restart_script.close()
            
            # Make executable
            os.chmod(restart_script.name, 0o755)
            
            print(f"🚀 Executing restart script: {restart_script.name}")
            
            # Execute restart script in background
            subprocess.Popen([restart_script.name], 
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           start_new_session=True)
            
            # Signal successful hook execution
            sys.exit(0)
        
        # If not meta-agent or no new agent created, do nothing
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Restart hook error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()