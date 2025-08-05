#!/usr/bin/env python3
"""
Minimal Strategic Flow Logger
Tracks only the essential 4-step dynamic agent flow progression
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def log_step(step_num, event, data=None):
    """Log essential flow progression events only
    
    Args:
        step_num (int): 1-4 corresponding to the 4-step flow
        event (str): Brief description of what happened
        data (dict, optional): Essential data only (agent names, status, etc.)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format log entry
    log_entry = f"{timestamp} [STEP-{step_num}] {event}"
    if data:
        # Only include essential fields to avoid noise
        essential_data = {k: v for k, v in data.items() if k in [
            'agent_name', 'subagent_type', 'completion_signal', 'mcp_status', 
            'restart_status', 'task_preview', 'error'
        ]}
        if essential_data:
            log_entry += f": {json.dumps(essential_data, separators=(',', ':'))}"
    
    # Write to single flow log file
    log_file = Path("flow_progress.log")
    try:
        with open(log_file, 'a') as f:
            f.write(log_entry + "\n")
    except Exception as e:
        # Fallback to stderr if file logging fails
        print(f"[FLOW-LOG-ERROR] {log_entry} (file error: {e})", file=sys.stderr)
        return
    
    # Also output to stderr for immediate visibility
    print(f"🔄 {log_entry}", file=sys.stderr)


def log_step_1(event, data=None):
    """Step 1: Primary agent delegates to meta-agent via Task tool"""
    log_step(1, event, data)


def log_step_2(event, data=None):
    """Step 2: Meta-agent creates specialist and outputs completion signal"""
    log_step(2, event, data)


def log_step_3(event, data=None):
    """Step 3: Hook detects completion → registers MCP → signals restart"""
    log_step(3, event, data)


def log_step_4(event, data=None):
    """Step 4: Fresh session starts → new subagent visible → task delegated"""
    log_step(4, event, data)


def log_error(step_num, error, data=None):
    """Log errors in the flow progression"""
    error_data = {"error": str(error)}
    if data:
        error_data.update(data)
    log_step(step_num, "ERROR", error_data)


def clear_flow_log():
    """Clear the flow log file (for fresh test runs)"""
    log_file = Path("flow_progress.log")
    try:
        log_file.unlink(missing_ok=True)
        print("🗑️  Flow log cleared", file=sys.stderr)
    except Exception as e:
        print(f"❌ Could not clear flow log: {e}", file=sys.stderr)


def show_flow_log():
    """Display the current flow log contents"""
    log_file = Path("flow_progress.log")
    if not log_file.exists():
        print("📝 Flow log is empty", file=sys.stderr)
        return
    
    print("📋 Current Flow Log:", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    try:
        with open(log_file, 'r') as f:
            for line in f:
                print(line.rstrip(), file=sys.stderr)
    except Exception as e:
        print(f"❌ Could not read flow log: {e}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == '__main__':
    # CLI interface for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Flow Logger Utility")
    parser.add_argument('--clear', action='store_true', help="Clear flow log")
    parser.add_argument('--show', action='store_true', help="Show flow log")
    parser.add_argument('--test', action='store_true', help="Test logging")
    
    args = parser.parse_args()
    
    if args.clear:
        clear_flow_log()
    elif args.show:
        show_flow_log()
    elif args.test:
        # Test the logging functions
        print("🧪 Testing flow logger...", file=sys.stderr)
        clear_flow_log()
        log_step_1("Primary agent delegates to meta-agent", {"subagent_type": "meta-agent"})
        log_step_2("Meta-agent completion detected", {"agent_name": "calculator", "completion_signal": "✅ **AGENT_CREATED**: calculator specialized for math"})
        log_step_3("MCP registration successful", {"mcp_status": "1 server registered"})
        log_step_4("Fresh session started", {"agent_name": "calculator"})
        show_flow_log()
    else:
        parser.print_help()