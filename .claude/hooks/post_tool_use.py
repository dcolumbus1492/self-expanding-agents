#!/usr/bin/env python3
"""
🔥 FIXED Phoenix Pattern Hook - ACTUALLY RESTARTS CLAUDE
Simple, bulletproof restart mechanism
"""

import json
import sys
import os
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime


def trigger_actual_restart():
    """ACTUALLY restart Claude - not just create a file"""
    
    print("🔥 PHOENIX RESTART: EXECUTING ACTUAL RESTART", file=sys.stderr)
    
    # Create restart script
    restart_script = tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.sh',
        prefix='phoenix_restart_',
        delete=False
    )
    
    working_dir = os.getcwd()
    
    restart_script.write(f'''#!/bin/bash
# Phoenix Pattern Restart - FIXED VERSION
echo "🔥 PHOENIX RESTART: Killing current session..."

# Kill current Claude process 
pkill -f "claude.*" || true
sleep 2

echo "🚀 PHOENIX RESTART: Restarting with --continue..."
cd "{working_dir}"

# Execute restart with --continue
claude --continue

echo "✅ PHOENIX RESTART: Complete!"
''')
    
    restart_script.flush()
    restart_script.close()
    
    # Make executable
    os.chmod(restart_script.name, 0o755)
    
    print(f"🚀 EXECUTING RESTART SCRIPT: {restart_script.name}", file=sys.stderr)
    
    # Execute restart in background - THIS WILL ACTUALLY RESTART
    subprocess.Popen([restart_script.name], start_new_session=True)
    
    # Exit current process to allow restart
    print("💀 EXITING CURRENT SESSION FOR RESTART", file=sys.stderr)
    os._exit(0)  # Force exit to trigger restart


def main():
    """Fixed Phoenix Pattern hook - simple and reliable"""
    
    print("🔧 FIXED HOOK STARTED", file=sys.stderr)
    
    try:
        # Read input
        input_data = json.loads(sys.stdin.read())
        
        # Check for Task tool with meta-agent
        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})
        tool_response = input_data.get('tool_response', {})
        subagent_type = tool_input.get('subagent_type', '')
        
        print(f"🔍 TOOL: {tool_name}, SUBAGENT: {subagent_type}", file=sys.stderr)
        
        if tool_name == "Task" and subagent_type == "meta-agent":
            print("✅ META-AGENT TASK DETECTED", file=sys.stderr)
            
            # Extract response text
            content = tool_response.get('content', [])
            if isinstance(content, list) and len(content) > 0:
                if isinstance(content[0], dict) and 'text' in content[0]:
                    result_text = content[0]['text']
                    result_lower = result_text.lower()
                    
                    print(f"📝 RESPONSE: {result_text[:100]}...", file=sys.stderr)
                    
                    # Check for agent creation pattern
                    if '✅ **agent created**' in result_lower:
                        print("🎯 PHOENIX PATTERN DETECTED - TRIGGERING RESTART!", file=sys.stderr)
                        
                        # Create indicator for debugging
                        Path("PHOENIX_RESTART_EXECUTED.txt").write_text(f"Phoenix restart executed at {datetime.now()}")
                        
                        # ACTUALLY RESTART CLAUDE
                        trigger_actual_restart()
                        
                    else:
                        print("❌ No agent creation pattern found", file=sys.stderr)
        
        print("🔧 HOOK COMPLETED (no restart needed)", file=sys.stderr)
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ HOOK ERROR: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()