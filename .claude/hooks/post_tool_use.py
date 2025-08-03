#!/usr/bin/env python3
"""
🔄 Dynamic Agent System - Post Tool Use Hook
Logs tool results and updates session tracking after tool execution
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime


def update_session_with_tool_result(session_dir, tool_data):
    """Update session tracking with tool execution results."""
    metadata_file = session_dir / "session_metadata.json"
    report_file = session_dir / "live_session_report.md"
    
    if not metadata_file.exists():
        return
    
    # Load current metadata
    with open(metadata_file, "r") as f:
        metadata = json.load(f)
    
    # Extract tool information
    tool_name = tool_data.get('tool_name', 'Unknown')
    result = tool_data.get('result', {})
    success = tool_data.get('success', True)
    error = tool_data.get('error', None)
    
    # Special handling for Task tool results (agent creation detection)
    if tool_name == "Task":
        subagent_type = tool_data.get('parameters', {}).get('subagent_type', '')
        
        # Check if this was a successful meta-agent task that likely created a new agent
        if subagent_type == 'meta-agent' and success:
            result_str = str(result).lower()
            if any(keyword in result_str for keyword in ['agent created', 'generated', 'specialized', 'subagent']):
                metadata["metrics"]["agents_created"] += 1
                metadata["agents"]["meta"]["creations"] += 1
                
                # Extract agent name if possible
                import re
                agent_match = re.search(r'(\w+)-agent|(\w+)_agent|agent[_-](\w+)', result_str)
                if agent_match:
                    agent_name = agent_match.group(1) or agent_match.group(2) or agent_match.group(3)
                    metadata["agents"]["specialized"][agent_name] = {
                        "created": datetime.now().isoformat(),
                        "status": "pending_restart"
                    }
    
    # Add completion event
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "tool_completion",
        "tool_name": tool_name,
        "success": success,
        "result_preview": str(result)[:300] + "..." if len(str(result)) > 300 else str(result),
        "error": error
    }
    metadata["events"].append(event)
    
    # Save updated metadata
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Update live report if it exists
    if report_file.exists():
        update_live_report_with_result(report_file, metadata, tool_name, result, success, error)


def update_live_report_with_result(report_file, metadata, tool_name, result, success, error):
    """Update the live session report with tool execution results."""
    with open(report_file, "r") as f:
        report_content = f.read()
    
    # Create timeline entry
    timestamp = datetime.now().strftime('%H:%M:%S')
    status = "✅" if success else "❌"
    details = f"{tool_name} completed {status}"
    if error:
        details += f" (Error: {str(error)[:50]})"
    
    timeline_entry = f"| {timestamp} | Tool Result | System | {details} |"
    
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
    
    # Update specialized agents section if agents were created
    specialized_agents_section = ""
    if metadata["agents"]["specialized"]:
        specialized_agents_section = "\n\n### Specialized Agents\n"
        for agent_name, agent_info in metadata["agents"]["specialized"].items():
            status_icon = "🟡" if agent_info["status"] == "pending_restart" else "🟢"
            specialized_agents_section += f"- **{agent_name}**: {status_icon} {agent_info['status'].replace('_', ' ').title()}\n"
    
    # Replace metrics
    import re
    metrics_pattern = r'### Key Metrics.*?(?=\n---|\n### |\Z)'
    updated_report = re.sub(metrics_pattern, metrics_section + specialized_agents_section, report_content, flags=re.DOTALL)
    
    # Add to timeline (insert before the tool usage log section)
    timeline_marker = "---\n\n## 🔧 Tool Usage Log"
    if timeline_marker in updated_report:
        timeline_section = updated_report.split(timeline_marker)[0]
        rest_section = timeline_marker + updated_report.split(timeline_marker)[1]
        
        # Add new timeline entry
        timeline_section += f"\n{timeline_entry}"
        updated_report = timeline_section + "\n\n" + rest_section
    
    # Update agent flow diagram if new agents were created
    if metadata["metrics"]["agents_created"] > 0:
        mermaid_with_specialized = """```mermaid
graph TD
    A[Primary Agent] --> B[User Request]
    B --> C{{Needs Specialized Agent?}}
    C -->|Yes| D[Meta-Agent]
    C -->|No| E[Direct Response]
    D --> F[Agent Creation ✅]
    F --> G[Hook Restart]
    G --> H[Specialized Agent]
    H --> I[Task Completion]
    
    style F fill:#90EE90
    style H fill:#FFE4B5
```"""
        
        mermaid_pattern = r'```mermaid.*?```'
        updated_report = re.sub(mermaid_pattern, mermaid_with_specialized, updated_report, flags=re.DOTALL)
    
    # Update timestamp
    timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    updated_report = re.sub(r'\*Last updated: .*?\*', f'*Last updated: {timestamp_now}*', updated_report)
    
    # Write updated report
    with open(report_file, "w") as f:
        f.write(updated_report)


def log_tool_result(session_dir, tool_data):
    """Log the tool result to session events."""
    events_file = session_dir / "session_events.json"
    
    if events_file.exists():
        with open(events_file, "r") as f:
            events_log = json.load(f)
    else:
        events_log = {"session_id": tool_data.get('session_id', 'unknown'), "events": []}
    
    # Add tool result event
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "post_tool_use",
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
    """Main post tool use hook handler."""
    try:
        # Read input data
        input_data = json.loads(sys.stdin.read())
        
        # Find session directory
        session_id = input_data.get('session_id', 'unknown')
        session_dir = find_session_directory(session_id)
        
        if session_dir:
            # Log the tool result
            log_tool_result(session_dir, input_data)
            
            # Update session tracking
            update_session_with_tool_result(session_dir, input_data)
            
            tool_name = input_data.get('tool_name', 'Unknown')
            success = input_data.get('success', True)
            status = "✅" if success else "❌"
            print(f"🔧 Post-tool result logged: {tool_name} {status} for session: {session_id}", file=sys.stderr)
        else:
            print(f"⚠️  Session directory not found for: {session_id}", file=sys.stderr)
        
        # Exit successfully
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Post tool use hook error: {e}", file=sys.stderr)
        sys.exit(0)  # Fail gracefully


if __name__ == '__main__':
    main()