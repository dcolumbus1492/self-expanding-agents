#!/usr/bin/env python3
"""
PreToolUse Hook - Log Tool Inputs
Captures tool inputs before execution in session_events.json
"""

import json
import sys
from pathlib import Path

# Import session logger
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from session_logger import log_pre_tool_use
except ImportError:
    # Fallback if import fails
    def log_pre_tool_use(data):
        print(f"[PRE-TOOL] {json.dumps(data)}", file=sys.stderr)


def main():
    """Log pre-tool use event to session events"""
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
            print(f"[PRE-TOOL-JSON-ERROR] {e}", file=sys.stderr)
            sys.exit(0)
        
        # Log the pre-tool use event
        log_pre_tool_use(input_data)
        
        # Exit successfully (allow tool to proceed)
        sys.exit(0)
        
    except Exception as e:
        print(f"[PRE-TOOL-ERROR] {e}", file=sys.stderr)
        sys.exit(0)  # Don't block Claude on logging errors


if __name__ == '__main__':
    main()