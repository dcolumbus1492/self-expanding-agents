#!/usr/bin/env python3
"""
PostToolUse Hook - Log Tool Outputs + Phoenix Restart Logic
1. Logs ALL tool outputs to session_events.json
2. Detects meta-agent completion for phoenix restart
"""

import json
import sys
import subprocess
import re
from pathlib import Path

# Import session logger
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from session_logger import log_post_tool_use
except ImportError:
    # Fallback if import fails
    def log_post_tool_use(data):
        print(f"[POST-TOOL] {json.dumps(data)}", file=sys.stderr)


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
        print(f"[PHOENIX] MCP registration script not found: {script_path}", file=sys.stderr)
        return False
    
    try:
        # Run the MCP registration script
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("[PHOENIX] MCP servers registered successfully", file=sys.stderr)
            return True
        else:
            print(f"[PHOENIX] MCP registration warnings: {result.stderr.strip()[:200]}", file=sys.stderr)
            return True  # Continue with restart anyway
            
    except Exception as e:
        print(f"[PHOENIX] MCP registration error: {e}", file=sys.stderr)
        return True  # Continue with restart anyway


def signal_phoenix_restart():
    """Signal the launcher that a restart is needed"""
    try:
        # Create the restart marker file
        marker_file = Path(".restart_needed")
        marker_file.touch()
        
        print(f"[PHOENIX] Restart marker created: {marker_file}", file=sys.stderr)
        return True
        
    except Exception as e:
        print(f"[PHOENIX] Failed to signal restart: {e}", file=sys.stderr)
        return False


def main():
    """Log post-tool use event + handle phoenix restart logic"""
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
            print(f"[POST-TOOL-JSON-ERROR] {e}", file=sys.stderr)
            sys.exit(0)
        
        # ALWAYS log the post-tool event first
        log_post_tool_use(input_data)
        
        # Extract tool information for phoenix logic
        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})
        tool_response = input_data.get('tool_response', {})
        subagent_type = tool_input.get('subagent_type', '')
        
        # PHOENIX LOGIC: Only process Task tool calls to meta-agent
        if tool_name == "Task" and subagent_type == "meta-agent":
            print(f"[PHOENIX] Meta-agent Task detected", file=sys.stderr)
            
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
            
            # Log the response for debugging
            print(f"[PHOENIX] Meta-agent response preview: {response_text[:200]}...", file=sys.stderr)
            
            # Detect agent creation completion
            completion_detected, completion_data = detect_agent_creation_completion(response_text)
            
            if completion_detected:
                print(f"[PHOENIX] Agent creation detected: {completion_data['agent_name']}", file=sys.stderr)
                
                # Register MCP servers
                mcp_success = register_mcp_servers()
                
                # Signal restart
                restart_success = signal_phoenix_restart()
                
                if restart_success:
                    print(f"[PHOENIX] Phoenix restart sequence completed", file=sys.stderr)
                else:
                    print(f"[PHOENIX] Phoenix restart sequence failed", file=sys.stderr)
                    
            else:
                # Fallback: Check if files were created even without completion signal
                agents_dir = Path(".claude/agents")
                mcp_dir = Path("dynamic_agents/generated_mcp")
                
                files_created = (
                    agents_dir.exists() and 
                    len(list(agents_dir.glob("*.md"))) > 1 and  # More than just meta-agent.md
                    mcp_dir.exists() and
                    len(list(mcp_dir.glob("*.py"))) > 0
                )
                
                if files_created:
                    print("[PHOENIX] Agent creation detected via file creation (no completion signal)", file=sys.stderr)
                    
                    # Still trigger the restart sequence
                    mcp_success = register_mcp_servers()
                    restart_success = signal_phoenix_restart()
                    
                    if restart_success:
                        print("[PHOENIX] Phoenix restart sequence completed (fallback)", file=sys.stderr)
                else:
                    print("[PHOENIX] No agent creation detected", file=sys.stderr)
        
        # Exit successfully
        sys.exit(0)
        
    except Exception as e:
        print(f"[POST-TOOL-ERROR] {e}", file=sys.stderr)
        sys.exit(0)  # Don't block Claude on logging errors


if __name__ == '__main__':
    main()