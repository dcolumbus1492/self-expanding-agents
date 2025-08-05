#!/usr/bin/env python3
"""
Phoenix Restart Hook - Minimal and Focused
Detects meta-agent completion → registers MCP → signals restart

CRITICAL: This hook must reliably catch the exact moment when meta-agent finishes
"""

import json
import sys
import subprocess
import re
from pathlib import Path

# Import flow logger for strategic logging
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from flow_logger import log_step_2, log_step_3, log_error
except ImportError:
    # Fallback if flow_logger not available
    def log_step_2(event, data=None):
        print(f"[STEP-2] {event}", file=sys.stderr)
    def log_step_3(event, data=None):
        print(f"[STEP-3] {event}", file=sys.stderr)
    def log_error(step, error, data=None):
        print(f"[ERROR-{step}] {error}", file=sys.stderr)


def detect_agent_creation_completion(response_text):
    """Detect the exact meta-agent completion pattern
    
    Pattern: ✅ **AGENT_CREATED**: [name] specialized for [purpose]
    """
    if not response_text:
        return False, None
        
    # Look for the exact completion pattern
    pattern = r'✅\s*\*\*AGENT_CREATED\*\*:\s*([\w-]+)\s+specialized\s+for\s+(.*?)(?:\n|$)'
    match = re.search(pattern, response_text, re.IGNORECASE | re.MULTILINE)
    
    if match:
        agent_name = match.group(1)
        purpose = match.group(2).strip()
        return True, {"agent_name": agent_name, "purpose": purpose}
    
    return False, None


def register_mcp_servers():
    """Register MCP servers using the existing registration script"""
    script_path = Path("dynamic_agents/register_mcp.py")
    
    if not script_path.exists():
        log_error(3, "MCP registration script not found", {"script_path": str(script_path)})
        return False
    
    try:
        # Run the MCP registration script
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            log_step_3("MCP servers registered successfully", {
                "mcp_status": "registration completed"
            })
            return True
        else:
            # Log warning but don't fail - restart can still work without MCP
            log_step_3("MCP registration had issues but continuing", {
                "mcp_status": "registration warnings",
                "error": result.stderr.strip()[:100]
            })
            return True  # Continue with restart anyway
            
    except Exception as e:
        log_error(3, f"MCP registration error: {e}")
        return True  # Continue with restart anyway


def signal_phoenix_restart():
    """Signal the launcher that a restart is needed"""
    try:
        # Create the restart marker file
        marker_file = Path(".restart_needed")
        marker_file.touch()
        
        log_step_3("Phoenix restart signaled", {
            "restart_status": "marker created",
            "marker_file": str(marker_file)
        })
        
        return True
        
    except Exception as e:
        log_error(3, f"Failed to signal restart: {e}")
        return False


def main():
    """Phoenix Pattern: Detect meta-agent completion → Register MCP → Signal restart"""
    try:
        # Read the hook input data
        if sys.stdin.isatty():
            # No input data available
            sys.exit(0)
            
        input_text = sys.stdin.read().strip()
        if not input_text:
            sys.exit(0)
            
        # Parse the JSON input
        try:
            input_data = json.loads(input_text)
        except json.JSONDecodeError as e:
            log_error(3, f"JSON parse error: {e}")
            sys.exit(0)
        
        # Extract tool information
        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})
        tool_response = input_data.get('tool_response', {})
        subagent_type = tool_input.get('subagent_type', '')
        
        # CRITICAL CHECK: Only process Task tool calls to meta-agent
        if tool_name != "Task" or subagent_type != "meta-agent":
            # Not a meta-agent task - exit silently
            sys.exit(0)
            
        log_step_2("Meta-agent Task tool call detected", {
            "subagent_type": subagent_type
        })
        
        # Extract the response text from the meta-agent
        response_text = ""
        if isinstance(tool_response, dict):
            content = tool_response.get('content', [])
            if isinstance(content, list) and len(content) > 0:
                if isinstance(content[0], dict) and 'text' in content[0]:
                    response_text = content[0]['text']
        
        # Convert to string if needed
        if not isinstance(response_text, str):
            response_text = str(tool_response)
            
        # Detect agent creation completion
        completion_detected, completion_data = detect_agent_creation_completion(response_text)
        
        if completion_detected:
            log_step_2("Agent creation completion detected", {
                "completion_signal": f"✅ **AGENT_CREATED**: {completion_data['agent_name']} specialized for {completion_data['purpose'][:50]}...",
                "agent_name": completion_data['agent_name']
            })
            
            # Step 3a: Register MCP servers
            mcp_success = register_mcp_servers()
            
            # Step 3b: Signal restart (regardless of MCP result)
            restart_success = signal_phoenix_restart()
            
            if restart_success:
                log_step_3("Phoenix restart sequence completed", {
                    "mcp_status": "success" if mcp_success else "warnings",
                    "restart_status": "signaled"
                })
            else:
                log_error(3, "Phoenix restart sequence failed")
                
        else:
            # Check if files were created even without completion signal
            # This is a fallback for cases where meta-agent doesn't output the signal
            agents_dir = Path(".claude/agents")
            mcp_dir = Path("dynamic_agents/generated_mcp")
            
            files_created = (
                agents_dir.exists() and 
                len(list(agents_dir.glob("*.md"))) > 1 and  # More than just meta-agent.md
                mcp_dir.exists() and
                len(list(mcp_dir.glob("*.py"))) > 0
            )
            
            if files_created:
                log_step_2("Agent creation detected via file creation (no completion signal)", {
                    "agent_name": "unknown",
                    "completion_signal": "file creation fallback"
                })
                
                # Still trigger the restart sequence
                mcp_success = register_mcp_servers()
                restart_success = signal_phoenix_restart()
                
                if restart_success:
                    log_step_3("Phoenix restart sequence completed (fallback)", {
                        "mcp_status": "success" if mcp_success else "warnings",
                        "restart_status": "signaled"
                    })
            else:
                # Meta-agent task completed but no agent was created
                # This is normal for some meta-agent calls
                pass
        
        sys.exit(0)
        
    except Exception as e:
        log_error(3, f"Phoenix hook error: {e}")
        sys.exit(0)  # Always exit gracefully to avoid breaking Claude


if __name__ == '__main__':
    main()