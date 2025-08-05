#!/usr/bin/env python3
"""
SubagentStop Hook - Detect Meta-Agent Completion
Triggers when meta-agent subagent task completes
"""

import json
import sys
import subprocess
from pathlib import Path

# Import session logger
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from session_logger import log_step_3
except ImportError:
    # Fallback if import fails
    def log_step_3(event, data=None):
        print(f"[SUBAGENT-STOP] {event}", file=sys.stderr)


def register_mcp_servers():
    """Register MCP servers using the existing registration script"""
    script_path = Path("dynamic_agents/register_mcp.py")
    
    if not script_path.exists():
        print(f"[SUBAGENT-STOP] MCP registration script not found: {script_path}", file=sys.stderr)
        return False
    
    try:
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("[SUBAGENT-STOP] MCP servers registered successfully", file=sys.stderr)
            return True
        else:
            print(f"[SUBAGENT-STOP] MCP registration warnings: {result.stderr.strip()[:200]}", file=sys.stderr)
            return True  # Continue with restart anyway
            
    except Exception as e:
        print(f"[SUBAGENT-STOP] MCP registration error: {e}", file=sys.stderr)
        return True  # Continue with restart anyway


def signal_phoenix_restart():
    """Signal the launcher that a restart is needed"""
    try:
        marker_file = Path(".restart_needed")
        marker_file.touch()
        
        print(f"[SUBAGENT-STOP] Restart marker created: {marker_file}", file=sys.stderr)
        return True
        
    except Exception as e:
        print(f"[SUBAGENT-STOP] Failed to signal restart: {e}", file=sys.stderr)
        return False


def main():
    """Handle subagent stop events"""
    try:
        # Read input from stdin
        if sys.stdin.isatty():
            sys.exit(0)
            
        input_text = sys.stdin.read().strip()
        if not input_text:
            sys.exit(0)
        
        # Parse JSON input
        try:
            input_data = json.loads(input_text)
        except json.JSONDecodeError as e:
            print(f"[SUBAGENT-STOP-JSON-ERROR] {e}", file=sys.stderr)
            sys.exit(0)
        
        print(f"[SUBAGENT-STOP] Subagent stopped: {json.dumps(input_data, indent=2)}", file=sys.stderr)
        
        # Log the subagent stop event
        log_step_3("Subagent stop detected", {"data": input_data})
        
        # Check if this is the meta-agent stopping
        # The exact structure of subagent stop data needs to be determined
        # For now, trigger phoenix restart on any subagent stop
        
        print("[SUBAGENT-STOP] Triggering Phoenix restart sequence", file=sys.stderr)
        
        # Register MCP servers
        mcp_success = register_mcp_servers()
        
        # Signal restart
        restart_success = signal_phoenix_restart()
        
        if restart_success:
            print("[SUBAGENT-STOP] Phoenix restart sequence completed", file=sys.stderr)
            log_step_3("Phoenix restart triggered via SubagentStop", {
                "mcp_status": "success" if mcp_success else "warnings",
                "restart_status": "signaled"
            })
        else:
            print("[SUBAGENT-STOP] Phoenix restart sequence failed", file=sys.stderr)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"[SUBAGENT-STOP-ERROR] {e}", file=sys.stderr)
        sys.exit(0)  # Don't block Claude on logging errors


if __name__ == '__main__':
    main()