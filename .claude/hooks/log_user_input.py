#!/usr/bin/env python3
"""
UserPromptSubmit Hook - Log User Inputs
Captures user prompts/questions in session_events.json
"""

import json
import sys
from pathlib import Path

# Import session logger
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from session_logger import log_user_input
except ImportError:
    # Fallback if import fails
    def log_user_input(data):
        print(f"[USER-INPUT] {json.dumps(data)}", file=sys.stderr)


def main():
    """Log user prompt submission to session events"""
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
        except json.JSONDecodeError:
            # If not JSON, treat as plain text
            input_data = {"raw_input": input_text}
        
        # Log the user input event
        log_user_input(input_data)
        
        # Exit successfully
        sys.exit(0)
        
    except Exception as e:
        print(f"[USER-INPUT-ERROR] {e}", file=sys.stderr)
        sys.exit(0)  # Don't block Claude on logging errors


if __name__ == '__main__':
    main()