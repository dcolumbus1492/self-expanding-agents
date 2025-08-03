#!/usr/bin/env python3
"""
🔄 Dynamic Agent System - Session Start Hook
Initializes comprehensive session logging and context tracking
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
import uuid


def create_session_report_template(session_data):
    """Create the initial session report markdown file."""
    session_id = session_data.get('session_id', str(uuid.uuid4())[:8])
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    source = session_data.get('source', 'unknown')
    
    template = f"""# 🔄 Dynamic Agent Session Report
**Session ID**: `{session_id}`
**Started**: {timestamp}
**Source**: {source}
**Status**: 🟢 Active

---

## 📊 Session Overview

### Agent Flow
```mermaid
graph TD
    A[Primary Agent] --> B[User Request]
    B --> C{{Needs Specialized Agent?}}
    C -->|Yes| D[Meta-Agent]
    C -->|No| E[Direct Response]
    D --> F[Agent Creation]
    F --> G[Hook Restart]
    G --> H[Specialized Agent]
    H --> I[Task Completion]
```

### Key Metrics
- **Total Interactions**: 0
- **Agents Created**: 0
- **Tools Used**: 0
- **Restarts**: 0

---

## 🎭 Agent Interactions

### Primary Agent
- **Status**: Active
- **Role**: Pure orchestrator and delegator
- **Allowed Tools**: Task only
- **Interactions**: 0

---

## 📝 Session Timeline

| Time | Event | Agent | Details |
|------|-------|-------|---------|
| {timestamp} | Session Started | System | {source} session initialized |

---

## 🔧 Tool Usage Log

*No tools used yet*

---

## 📊 Session Statistics

- **Session Duration**: Just started
- **Message Count**: 0
- **Successful Delegations**: 0
- **Agent Creations**: 0
- **Hook Triggers**: 0

---

## 🎯 Current Status

**Active Session** - Ready for user interaction

*Last updated: {timestamp}*
"""
    
    return template


def initialize_session_logging(session_data):
    """Initialize comprehensive session logging structure."""
    
    # Create logs directory structure
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Session-specific directory with timestamp for easy sorting
    session_id = session_data.get('session_id', str(uuid.uuid4())[:8])
    timestamp_prefix = datetime.now().strftime('%Y%m%d_%H%M%S')
    session_dir = logs_dir / f"session_{timestamp_prefix}_{session_id}"
    session_dir.mkdir(exist_ok=True)
    
    # Create session metadata
    session_meta = {
        "session_id": session_id,
        "start_time": datetime.now().isoformat(),
        "source": session_data.get('source', 'unknown'),
        "status": "active",
        "events": [],
        "agents": {
            "primary": {"status": "active", "interactions": 0},
            "meta": {"status": "ready", "creations": 0},
            "specialized": {}
        },
        "metrics": {
            "total_interactions": 0,
            "agents_created": 0,
            "tools_used": 0,
            "restarts": 0,
            "hook_triggers": 0
        }
    }
    
    # Save session metadata
    with open(session_dir / "session_metadata.json", "w") as f:
        json.dump(session_meta, f, indent=2)
    
    # Create live session report
    report_content = create_session_report_template(session_data)
    with open(session_dir / "live_session_report.md", "w") as f:
        f.write(report_content)
    
    # Create main session log
    session_log = {
        "session_id": session_id,
        "events": [
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": "session_start",
                "source": session_data.get('source', 'unknown'),
                "data": session_data
            }
        ]
    }
    
    with open(session_dir / "session_events.json", "w") as f:
        json.dump(session_log, f, indent=2)
    
    # Update global session registry
    registry_file = logs_dir / "session_registry.json"
    if registry_file.exists():
        with open(registry_file, "r") as f:
            registry = json.load(f)
    else:
        registry = {"sessions": []}
    
    # Add or update session in registry
    session_entry = {
        "session_id": session_id,
        "start_time": datetime.now().isoformat(),
        "source": session_data.get('source', 'unknown'),
        "status": "active",
        "report_path": str(session_dir / "live_session_report.md")
    }
    
    # Remove any existing entry for this session
    registry["sessions"] = [s for s in registry["sessions"] if s["session_id"] != session_id]
    registry["sessions"].append(session_entry)
    
    with open(registry_file, "w") as f:
        json.dump(registry, f, indent=2)
    
    return session_dir


def get_git_context():
    """Get current git context for session initialization."""
    try:
        import subprocess
        
        # Get current branch
        branch_result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True, text=True, timeout=5
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
        
        # Get status
        status_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True, timeout=5
        )
        if status_result.returncode == 0:
            changes = len(status_result.stdout.strip().split('\n')) if status_result.stdout.strip() else 0
        else:
            changes = 0
        
        # Get last commit
        commit_result = subprocess.run(
            ['git', 'log', '-1', '--oneline'],
            capture_output=True, text=True, timeout=5
        )
        last_commit = commit_result.stdout.strip() if commit_result.returncode == 0 else "No commits"
        
        return {
            "branch": branch,
            "uncommitted_changes": changes,
            "last_commit": last_commit
        }
    except Exception:
        return {"branch": "unknown", "uncommitted_changes": 0, "last_commit": "unknown"}


def main():
    """Main session start hook handler."""
    try:
        # Read input data
        input_data = json.loads(sys.stdin.read())
        
        # Add git context
        input_data["git_context"] = get_git_context()
        
        # Initialize comprehensive logging
        session_dir = initialize_session_logging(input_data)
        
        # Print session info to stderr for debugging
        session_id = input_data.get('session_id', 'unknown')
        print(f"🔄 Session logging initialized: {session_id}", file=sys.stderr)
        print(f"📁 Session directory: {session_dir}", file=sys.stderr)
        print(f"📊 Live report: {session_dir}/live_session_report.md", file=sys.stderr)
        
        # Exit successfully
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Session start hook error: {e}", file=sys.stderr)
        sys.exit(0)  # Fail gracefully


if __name__ == '__main__':
    main()