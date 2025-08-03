#!/usr/bin/env python3
"""
🔄 Dynamic Agent System - Pre Tool Use Hook
Logs tool usage before execution and updates session tracking
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime


def update_session_with_tool_use(session_dir, tool_data):
    """Update session tracking with tool usage information."""
    metadata_file = session_dir / "session_metadata.json"
    report_file = session_dir / "live_session_report.md"
    
    if not metadata_file.exists():
        return
    
    # Load current metadata
    with open(metadata_file, "r") as f:
        metadata = json.load(f)
    
    # Extract tool information
    tool_name = tool_data.get('tool_name', 'Unknown')
    tool_parameters = tool_data.get('parameters', {})
    agent_type = tool_data.get('agent_type', 'unknown')
    
    # Update metrics
    metadata["metrics"]["tools_used"] += 1
    
    # Special handling for Task tool (delegation detection)
    if tool_name == "Task":
        subagent_type = tool_parameters.get('subagent_type', '')
        if subagent_type == 'meta-agent':
            metadata["agents"]["meta"]["status"] = "active"
            # This indicates primary agent is delegating to meta-agent
            event_type = "delegation_to_meta"
        else:
            event_type = "delegation_to_specialized"
    else:
        event_type = "tool_use"
    
    # Add event
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "tool_name": tool_name,
        "agent_type": agent_type,
        "parameters_summary": str(tool_parameters)[:200] + "..." if len(str(tool_parameters)) > 200 else str(tool_parameters)
    }
    metadata["events"].append(event)
    
    # Save updated metadata
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Update live report if it exists
    if report_file.exists():
        update_live_report_with_tool(report_file, metadata, tool_name, tool_parameters, event_type)


def update_live_report_with_tool(report_file, metadata, tool_name, tool_parameters, event_type):
    """Update the live session report with tool usage."""
    with open(report_file, "r") as f:
        report_content = f.read()
    
    # Create timeline entry
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    if event_type == "delegation_to_meta":
        agent_name = "Primary Agent"
        details = f"Delegating to meta-agent: {tool_parameters.get('description', 'Task delegation')}"
        timeline_entry = f"| {timestamp} | Delegation | {agent_name} | {details} |"
    elif event_type == "delegation_to_specialized":
        agent_name = "Primary Agent"
        subagent_type = tool_parameters.get('subagent_type', 'Unknown')
        details = f"Delegating to {subagent_type}: {tool_parameters.get('description', 'Task delegation')}"
        timeline_entry = f"| {timestamp} | Delegation | {agent_name} | {details} |"
    else:
        agent_name = "Agent"
        details = f"Using {tool_name} tool"
        timeline_entry = f"| {timestamp} | Tool Use | {agent_name} | {details} |"
    
    # Update metrics section
    tools_used = metadata["metrics"]["tools_used"]
    agents_created = metadata["metrics"]["agents_created"]
    total_interactions = metadata["metrics"]["total_interactions"]
    restarts = metadata["metrics"]["restarts"]
    
    metrics_section = f"""### Key Metrics
- **Total Interactions**: {total_interactions}
- **Agents Created**: {agents_created}
- **Tools Used**: {tools_used}
- **Restarts**: {restarts}"""
    
    # Replace metrics
    import re
    metrics_pattern = r'### Key Metrics.*?(?=\n---|\n### |\Z)'
    updated_report = re.sub(metrics_pattern, metrics_section, report_content, flags=re.DOTALL)
    
    # Add to timeline (insert before the tool usage log section)
    timeline_marker = "---\n\n## 🔧 Tool Usage Log"
    if timeline_marker in updated_report:
        timeline_section = updated_report.split(timeline_marker)[0]
        rest_section = timeline_marker + updated_report.split(timeline_marker)[1]
        
        # Add new timeline entry
        timeline_section += f"\n{timeline_entry}"
        updated_report = timeline_section + "\n\n" + rest_section
    
    # Update tool usage log section
    tool_usage_pattern = r'## 🔧 Tool Usage Log\s*\n\n\*No tools used yet\*'
    if re.search(tool_usage_pattern, updated_report):
        # First tool usage
        tool_log_section = f"""## 🔧 Tool Usage Log

### {tool_name}
- **Used**: {datetime.now().strftime('%H:%M:%S')}
- **Type**: {event_type.replace('_', ' ').title()}
- **Parameters**: {str(tool_parameters)[:100]}{"..." if len(str(tool_parameters)) > 100 else ""}"""
        updated_report = re.sub(tool_usage_pattern, tool_log_section, updated_report)
    else:
        # Add to existing tool usage
        tool_entry = f"""
### {tool_name}
- **Used**: {datetime.now().strftime('%H:%M:%S')}
- **Type**: {event_type.replace('_', ' ').title()}
- **Parameters**: {str(tool_parameters)[:100]}{"..." if len(str(tool_parameters)) > 100 else ""}"""
        
        # Find the tool usage section and add the entry
        tool_section_end = "---\n\n## 📊 Session Statistics"
        if tool_section_end in updated_report:
            parts = updated_report.split(tool_section_end)
            updated_report = parts[0] + tool_entry + "\n\n" + tool_section_end + parts[1]
    
    # Update timestamp
    timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    updated_report = re.sub(r'\*Last updated: .*?\*', f'*Last updated: {timestamp_now}*', updated_report)
    
    # Write updated report
    with open(report_file, "w") as f:
        f.write(updated_report)


def log_tool_use(session_dir, tool_data):
    """Log the tool use to session events."""
    events_file = session_dir / "session_events.json"
    
    if events_file.exists():
        with open(events_file, "r") as f:
            events_log = json.load(f)
    else:
        events_log = {"session_id": tool_data.get('session_id', 'unknown'), "events": []}
    
    # Add tool use event
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "pre_tool_use",
        "data": tool_data
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
    """Main pre tool use hook handler."""
    try:
        # Read input data
        input_data = json.loads(sys.stdin.read())
        
        # Find session directory
        session_id = input_data.get('session_id', 'unknown')
        session_dir = find_session_directory(session_id)
        
        if session_dir:
            # Log the tool use
            log_tool_use(session_dir, input_data)
            
            # Update session tracking
            update_session_with_tool_use(session_dir, input_data)
            
            tool_name = input_data.get('tool_name', 'Unknown')
            print(f"🔧 Pre-tool use logged: {tool_name} for session: {session_id}", file=sys.stderr)
        else:
            print(f"⚠️  Session directory not found for: {session_id}", file=sys.stderr)
        
        # Exit successfully
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Pre tool use hook error: {e}", file=sys.stderr)
        sys.exit(0)  # Fail gracefully


if __name__ == '__main__':
    main()