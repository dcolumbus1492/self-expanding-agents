#!/usr/bin/env python3
"""
Session Event Logger - Simple JSON Event Stream
Captures ALL Claude Code session inputs/outputs in a single JSON file
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import fcntl


def log_session_event(event_type, data):
    """
    Log a session event to session_events.json
    
    Args:
        event_type (str): Type of event (user_prompt_submit, pre_tool_use, post_tool_use, session_stop)
        data (dict): The event data (complete hook input data)
    """
    
    # Create event entry
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "data": data
    }
    
    # Path to session events log
    log_file = Path("session_events.json")
    
    try:
        # Read existing events or create empty list
        if log_file.exists():
            with open(log_file, 'r') as f:
                try:
                    events = json.load(f)
                    if not isinstance(events, list):
                        events = []
                except json.JSONDecodeError:
                    events = []
        else:
            events = []
        
        # Add new event
        events.append(event)
        
        # Write back to file with file locking to prevent race conditions
        with open(log_file, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            json.dump(events, f, indent=2)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
    except Exception as e:
        # Fallback: write to stderr if file logging fails
        print(f"[SESSION-LOG-ERROR] {event_type}: {e}", file=sys.stderr)
        print(f"[SESSION-LOG-FALLBACK] {json.dumps(event)}", file=sys.stderr)


def log_user_input(user_data):
    """Log user prompt submission"""
    log_session_event("user_prompt_submit", user_data)


def log_pre_tool_use(tool_data):
    """Log pre-tool use event"""
    log_session_event("pre_tool_use", tool_data)


def log_post_tool_use(tool_data):
    """Log post-tool use event"""
    log_session_event("post_tool_use", tool_data)


def log_session_stop(stop_data):
    """Log session stop event"""
    log_session_event("session_stop", stop_data)


def clear_session_log():
    """Clear the session events log (for fresh sessions)"""
    log_file = Path("session_events.json")
    try:
        if log_file.exists():
            log_file.unlink()
        print("🗑️  Session events log cleared", file=sys.stderr)
    except Exception as e:
        print(f"❌ Could not clear session log: {e}", file=sys.stderr)


def show_session_log():
    """Display the current session events log"""
    log_file = Path("session_events.json")
    if not log_file.exists():
        print("📝 Session events log is empty", file=sys.stderr)
        return
    
    try:
        with open(log_file, 'r') as f:
            events = json.load(f)
        
        print("📋 Session Events Log:", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        for i, event in enumerate(events, 1):
            print(f"{i:2d}. [{event['timestamp']}] {event['event_type']}", file=sys.stderr)
            if event['event_type'] == 'user_prompt_submit' and 'prompt' in event['data']:
                print(f"    User: {event['data']['prompt'][:100]}...", file=sys.stderr)
            elif event['event_type'] in ['pre_tool_use', 'post_tool_use']:
                tool_name = event['data'].get('tool_name', 'unknown')
                print(f"    Tool: {tool_name}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        
    except Exception as e:
        print(f"❌ Could not read session log: {e}", file=sys.stderr)


if __name__ == '__main__':
    # CLI interface for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Session Event Logger")
    parser.add_argument('--clear', action='store_true', help="Clear session log")
    parser.add_argument('--show', action='store_true', help="Show session log")
    parser.add_argument('--test', action='store_true', help="Test logging")
    
    args = parser.parse_args()
    
    if args.clear:
        clear_session_log()
    elif args.show:
        show_session_log()
    elif args.test:
        # Test the logging functions
        print("🧪 Testing session logger...", file=sys.stderr)
        clear_session_log()
        log_user_input({"prompt": "calculate 4+4"})
        log_pre_tool_use({"tool_name": "Task", "tool_input": {"subagent_type": "meta-agent"}})
        log_post_tool_use({"tool_name": "Task", "tool_response": {"content": "Agent created"}})
        log_session_stop({"duration": "30s"})
        show_session_log()
    else:
        parser.print_help()