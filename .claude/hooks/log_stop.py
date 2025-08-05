#!/usr/bin/env python3
"""
Stop Hook - Log Session End
Captures session stop events in session_events.json
"""

import json
import sys
from pathlib import Path

# Import session logger
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from session_logger import log_session_stop
except ImportError:
    # Fallback if import fails
    def log_session_stop(data):
        print(f"[SESSION-STOP] {json.dumps(data)}", file=sys.stderr)


def main():
    """Log session stop event to session events"""
    try:
        # Read input from stdin
        if sys.stdin.isatty():
            sys.exit(0)
            
        input_text = sys.stdin.read().strip()
        if not input_text:
            # No input data, create basic stop event
            input_data = {"event": "session_stop"}
        else:
            # Parse JSON input
            try:
                input_data = json.loads(input_text)
            except json.JSONDecodeError:
                # If not JSON, treat as plain text
                input_data = {"raw_stop_data": input_text}
        
        # Log the session stop event
        log_session_stop(input_data)
        
        print("[SESSION-STOP] Session events logged", file=sys.stderr)
        
        # Exit successfully
        sys.exit(0)
        
    except Exception as e:
        print(f"[SESSION-STOP-ERROR] {e}", file=sys.stderr)
        sys.exit(0)  # Don't block Claude on logging errors


if __name__ == '__main__':
    main()