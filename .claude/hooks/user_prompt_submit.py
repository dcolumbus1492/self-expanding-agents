#!/usr/bin/env python3
"""
🔄 Dynamic Agent System - User Prompt Submit Hook
Logs user interactions and updates session report
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime


def update_session_report(session_dir, prompt_data):
    """Update the live session report with user prompt."""
    report_file = session_dir / "live_session_report.md"
    metadata_file = session_dir / "session_metadata.json"
    
    if not report_file.exists() or not metadata_file.exists():
        return
    
    # Load current metadata
    with open(metadata_file, "r") as f:
        metadata = json.load(f)
    
    # Update metrics
    metadata["metrics"]["total_interactions"] += 1
    metadata["agents"]["primary"]["interactions"] += 1
    
    # Add event
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "user_prompt",
        "prompt_preview": prompt_data.get('prompt', '')[:100] + "..." if len(prompt_data.get('prompt', '')) > 100 else prompt_data.get('prompt', ''),
        "prompt_length": len(prompt_data.get('prompt', ''))
    }
    metadata["events"].append(event)
    
    # Save updated metadata
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Read current report
    with open(report_file, "r") as f:
        report_content = f.read()
    
    # Extract key information
    session_id = metadata["session_id"]
    start_time = metadata["start_time"]
    total_interactions = metadata["metrics"]["total_interactions"]
    agents_created = metadata["metrics"]["agents_created"]
    tools_used = metadata["metrics"]["tools_used"]
    restarts = metadata["metrics"]["restarts"]
    
    # Create timeline entry
    timestamp = datetime.now().strftime('%H:%M:%S')
    prompt_preview = prompt_data.get('prompt', '')[:50] + "..." if len(prompt_data.get('prompt', '')) > 50 else prompt_data.get('prompt', '')
    timeline_entry = f"| {timestamp} | User Prompt | User | \"{prompt_preview}\" |"
    
    # Update metrics section
    metrics_section = f"""### Key Metrics
- **Total Interactions**: {total_interactions}
- **Agents Created**: {agents_created}
- **Tools Used**: {tools_used}
- **Restarts**: {restarts}"""
    
    # Update primary agent section
    primary_section = f"""### Primary Agent
- **Status**: Active
- **Role**: Pure orchestrator and delegator
- **Allowed Tools**: Task only
- **Interactions**: {metadata["agents"]["primary"]["interactions"]}"""
    
    # Update the report
    updated_report = report_content
    
    # Replace metrics
    import re
    metrics_pattern = r'### Key Metrics.*?(?=\n---|\n### |\Z)'
    updated_report = re.sub(metrics_pattern, metrics_section, updated_report, flags=re.DOTALL)
    
    # Replace primary agent section
    primary_pattern = r'### Primary Agent.*?(?=\n---|\n### |\Z)'
    updated_report = re.sub(primary_pattern, primary_section, updated_report, flags=re.DOTALL)
    
    # Add to timeline (insert before the statistics section)
    timeline_marker = "---\n\n## 🔧 Tool Usage Log"
    if timeline_marker in updated_report:
        timeline_section = updated_report.split(timeline_marker)[0]
        rest_section = timeline_marker + updated_report.split(timeline_marker)[1]
        
        # Add new timeline entry
        timeline_section += f"\n{timeline_entry}"
        updated_report = timeline_section + "\n\n" + rest_section
    
    # Update timestamp
    timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    updated_report = re.sub(r'\*Last updated: .*?\*', f'*Last updated: {timestamp_now}*', updated_report)
    
    # Write updated report
    with open(report_file, "w") as f:
        f.write(updated_report)


def log_user_prompt(session_dir, prompt_data):
    """Log the user prompt to session events."""
    events_file = session_dir / "session_events.json"
    
    if events_file.exists():
        with open(events_file, "r") as f:
            events_log = json.load(f)
    else:
        events_log = {"session_id": prompt_data.get('session_id', 'unknown'), "events": []}
    
    # Add prompt event
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "user_prompt_submit",
        "data": prompt_data
    }
    
    events_log["events"].append(event)
    
    with open(events_file, "w") as f:
        json.dump(events_log, f, indent=2)


def find_session_directory(session_id):
    """Find the session directory for the given session ID."""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return None
    
    # Try timestamped format first (new format)
    for session_path in logs_dir.glob(f"session_*_{session_id}"):
        if session_path.is_dir():
            return session_path
    
    # Fallback to old format for backward compatibility
    session_dir = logs_dir / f"session_{session_id}"
    if session_dir.exists():
        return session_dir
    
    # Fallback: look for any active session
    for session_path in logs_dir.glob("session_*"):
        if session_path.is_dir():
            metadata_file = session_path / "session_metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)
                    if metadata.get("status") == "active":
                        return session_path
                except:
                    continue
    
    return None


def main():
    """Main user prompt submit hook handler."""
    try:
        # Read input data
        input_data = json.loads(sys.stdin.read())
        
        # Find session directory
        session_id = input_data.get('session_id', 'unknown')
        session_dir = find_session_directory(session_id)
        
        if session_dir:
            # Log the prompt
            log_user_prompt(session_dir, input_data)
            
            # Update live report
            update_session_report(session_dir, input_data)
            
            print(f"🔄 User prompt logged for session: {session_id}", file=sys.stderr)
        else:
            print(f"⚠️  Session directory not found for: {session_id}", file=sys.stderr)
        
        # Exit successfully
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ User prompt hook error: {e}", file=sys.stderr)
        sys.exit(0)  # Fail gracefully


if __name__ == '__main__':
    main()