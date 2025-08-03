#!/usr/bin/env python3
"""
🔄 Dynamic Agent System - Stop Hook
Finalizes session logging when Claude Code stops
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime


def finalize_session(session_dir, stop_data):
    """Finalize the session when Claude Code stops."""
    metadata_file = session_dir / "session_metadata.json"
    report_file = session_dir / "live_session_report.md"
    
    if not metadata_file.exists():
        return
    
    # Load current metadata
    with open(metadata_file, "r") as f:
        metadata = json.load(f)
    
    # Update session status
    metadata["status"] = "completed"
    metadata["end_time"] = datetime.now().isoformat()
    
    # Calculate session duration
    if "start_time" in metadata:
        start_time = datetime.fromisoformat(metadata["start_time"])
        end_time = datetime.now()
        duration = end_time - start_time
        metadata["duration_seconds"] = int(duration.total_seconds())
        metadata["duration_human"] = str(duration).split('.')[0]  # Remove microseconds
    
    # Add final event
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "session_stop",
        "data": stop_data
    }
    metadata["events"].append(event)
    
    # Save updated metadata
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Update live report to final report
    if report_file.exists():
        finalize_live_report(report_file, metadata)
    
    # Update session registry
    update_session_registry(metadata)


def finalize_live_report(report_file, metadata):
    """Convert live report to final session summary."""
    with open(report_file, "r") as f:
        report_content = f.read()
    
    # Update status to completed
    status_pattern = r'(\*\*Status\*\*: )🟢 Active'
    report_content = re.sub(status_pattern, r'\1🔴 Completed', report_content)
    
    # Add final statistics
    session_duration = metadata.get("duration_human", "Unknown")
    total_events = len(metadata.get("events", []))
    
    final_stats = f"""
## 🏁 Final Session Summary

**Session Completed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Duration**: {session_duration}
**Total Events**: {total_events}

### Session Highlights
"""
    
    # Add session highlights based on what happened
    highlights = []
    if metadata["metrics"]["agents_created"] > 0:
        highlights.append(f"🎭 Created {metadata['metrics']['agents_created']} specialized agent(s)")
    if metadata["metrics"]["tools_used"] > 0:
        highlights.append(f"🔧 Used {metadata['metrics']['tools_used']} tools")
    if metadata["metrics"]["restarts"] > 0:
        highlights.append(f"🔄 Performed {metadata['metrics']['restarts']} restart(s)")
    if metadata["metrics"]["total_interactions"] > 0:
        highlights.append(f"💬 Processed {metadata['metrics']['total_interactions']} user interaction(s)")
    
    if highlights:
        for highlight in highlights:
            final_stats += f"\n- {highlight}"
    else:
        final_stats += "\n- Session completed without major events"
    
    # Insert final summary before the current status section
    import re
    current_status_pattern = r'## 🎯 Current Status.*?(?=\n\*Last updated:|\Z)'
    replacement = final_stats + "\n\n## 🎯 Final Status\n\n**Session Completed Successfully**"
    report_content = re.sub(current_status_pattern, replacement, report_content, flags=re.DOTALL)
    
    # Update timestamp
    timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report_content = re.sub(r'\*Last updated: .*?\*', f'*Session completed: {timestamp_now}*', report_content)
    
    # Write final report
    final_report_path = report_file.parent / "final_session_report.md"
    with open(final_report_path, "w") as f:
        f.write(report_content)
    
    # Also update the live report
    with open(report_file, "w") as f:
        f.write(report_content)


def update_session_registry(metadata):
    """Update the session registry with final session information."""
    logs_dir = Path("logs")
    registry_file = logs_dir / "session_registry.json"
    
    if registry_file.exists():
        with open(registry_file, "r") as f:
            registry = json.load(f)
    else:
        registry = {"sessions": []}
    
    # Update session entry
    session_id = metadata["session_id"]
    for session in registry["sessions"]:
        if session["session_id"] == session_id:
            session["status"] = "completed"
            session["end_time"] = metadata.get("end_time")
            session["duration"] = metadata.get("duration_human", "Unknown")
            session["final_report_path"] = str(Path("logs") / f"session_{session_id}" / "final_session_report.md")
            break
    
    with open(registry_file, "w") as f:
        json.dump(registry, f, indent=2)


def log_session_stop(session_dir, stop_data):
    """Log the session stop to session events."""
    events_file = session_dir / "session_events.json"
    
    if events_file.exists():
        with open(events_file, "r") as f:
            events_log = json.load(f)
    else:
        events_log = {"session_id": stop_data.get('session_id', 'unknown'), "events": []}
    
    # Add session stop event
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "session_stop",
        "data": stop_data
    }
    
    events_log["events"].append(event)
    
    with open(events_file, "w") as f:
        json.dump(events_log, f, indent=2)


def find_session_directory(session_id):
    """Find the session directory for the given session ID."""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return None
    
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
    """Main session stop hook handler."""
    try:
        # Read input data
        input_data = json.loads(sys.stdin.read())
        
        # Find session directory
        session_id = input_data.get('session_id', 'unknown')
        session_dir = find_session_directory(session_id)
        
        if session_dir:
            # Log the session stop
            log_session_stop(session_dir, input_data)
            
            # Finalize the session
            finalize_session(session_dir, input_data)
            
            print(f"🔄 Session finalized: {session_id}", file=sys.stderr)
            print(f"📁 Final report: {session_dir}/final_session_report.md", file=sys.stderr)
        else:
            print(f"⚠️  Session directory not found for: {session_id}", file=sys.stderr)
        
        # Exit successfully
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Session stop hook error: {e}", file=sys.stderr)
        sys.exit(0)  # Fail gracefully


if __name__ == '__main__':
    main()