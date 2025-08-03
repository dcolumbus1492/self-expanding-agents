#!/usr/bin/env python3
"""
🔄 Dynamic Agent System - SubagentStop Hook
Enhanced version that logs agent completion AND triggers restart for meta-agent
"""

import json
import sys
import os
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime


def update_session_with_subagent_stop(session_dir, stop_data):
    """Update session tracking when a subagent stops."""
    metadata_file = session_dir / "session_metadata.json"
    report_file = session_dir / "live_session_report.md"
    
    if not metadata_file.exists():
        return False
    
    # Load current metadata
    with open(metadata_file, "r") as f:
        metadata = json.load(f)
    
    # Extract subagent information
    subagent_type = stop_data.get('subagent_type', '')
    result = stop_data.get('result', '')
    
    # Determine if this was meta-agent creating a new specialized agent
    # Check both subagent_type and result content for agent creation
    result_str = str(result).lower()
    is_meta_agent_creation = (
        (subagent_type == 'meta-agent' or 'agent created' in result_str) and
        any(keyword in result_str for keyword in [
            'agent created', 'specialized for', '✅ **agent created**'
        ])
    )
    
    # Add completion event
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "subagent_stop",
        "subagent_type": subagent_type,
        "result_preview": str(result)[:200] + "..." if len(str(result)) > 200 else str(result),
        "agent_creation_detected": is_meta_agent_creation
    }
    metadata["events"].append(event)
    
    # Update agent status
    if subagent_type == 'meta-agent':
        metadata["agents"]["meta"]["status"] = "completed"
        if is_meta_agent_creation:
            metadata["metrics"]["agents_created"] += 1
    
    # Save updated metadata
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Update live report if it exists
    if report_file.exists():
        update_live_report_with_subagent_stop(report_file, metadata, subagent_type, result, is_meta_agent_creation)
    
    return is_meta_agent_creation


def update_live_report_with_subagent_stop(report_file, metadata, subagent_type, result, is_creation):
    """Update the live session report with subagent stop information."""
    with open(report_file, "r") as f:
        report_content = f.read()
    
    # Create timeline entry
    timestamp = datetime.now().strftime('%H:%M:%S')
    if is_creation:
        details = f"Meta-agent completed - New specialized agent created! 🎉"
        timeline_entry = f"| {timestamp} | Agent Creation | Meta-Agent | {details} |"
    else:
        details = f"{subagent_type} completed task"
        timeline_entry = f"| {timestamp} | Subagent Stop | {subagent_type} | {details} |"
    
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
    
    # Update meta-agent section
    meta_status = metadata["agents"]["meta"]["status"]
    meta_creations = metadata["agents"]["meta"]["creations"]
    meta_section = f"""### Meta-Agent
- **Status**: {meta_status.title()}
- **Agents Created**: {meta_creations}
- **Last Activity**: {datetime.now().strftime('%H:%M:%S')}"""
    
    # Replace metrics
    import re
    metrics_pattern = r'### Key Metrics.*?(?=\n---|\n### |\Z)'
    updated_report = re.sub(metrics_pattern, metrics_section, report_content, flags=re.DOTALL)
    
    # Add or update meta-agent section
    if "### Meta-Agent" in updated_report:
        meta_pattern = r'### Meta-Agent.*?(?=\n---|\n### |\Z)'
        updated_report = re.sub(meta_pattern, meta_section, updated_report, flags=re.DOTALL)
    else:
        # Insert meta-agent section after primary agent
        primary_pattern = r'(### Primary Agent.*?)(\n---|\n### |$)'
        updated_report = re.sub(primary_pattern, r'\1\n\n' + meta_section + r'\2', updated_report, flags=re.DOTALL)
    
    # Add to timeline
    timeline_marker = "---\n\n## 🔧 Tool Usage Log"
    if timeline_marker in updated_report:
        timeline_section = updated_report.split(timeline_marker)[0]
        rest_section = timeline_marker + updated_report.split(timeline_marker)[1]
        
        # Add new timeline entry
        timeline_section += f"\n{timeline_entry}"
        updated_report = timeline_section + "\n\n" + rest_section
    
    # If this is a creation event, add pending restart notice
    if is_creation:
        status_pattern = r'(\*\*Current Status\*\*\n\n).*?(Ready for user interaction)'
        restart_notice = r'\1**🔄 Agent Created - Restart Pending**\n\nNew specialized agent will be available after automatic restart.\n\n'
        updated_report = re.sub(status_pattern, restart_notice, updated_report, flags=re.DOTALL)
    
    # Update timestamp
    timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    updated_report = re.sub(r'\*Last updated: .*?\*', f'*Last updated: {timestamp_now}*', updated_report)
    
    # Write updated report
    with open(report_file, "w") as f:
        f.write(updated_report)


def log_subagent_stop(session_dir, stop_data):
    """Log the subagent stop to session events."""
    events_file = session_dir / "session_events.json"
    
    if events_file.exists():
        with open(events_file, "r") as f:
            events_log = json.load(f)
    else:
        events_log = {"session_id": stop_data.get('session_id', 'unknown'), "events": []}
    
    # Add subagent stop event
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "subagent_stop",
        "data": stop_data
    }
    
    events_log["events"].append(event)
    
    with open(events_file, "w") as f:
        json.dump(events_log, f, indent=2)


def trigger_restart_for_meta_agent(stop_data, session_dir):
    """Trigger restart when meta-agent creates new specialized agent."""
    session_id = stop_data.get('session_id', '')
    working_dir = os.getcwd()
    
    # Update session metadata to indicate restart is happening
    metadata_file = session_dir / "session_metadata.json"
    if metadata_file.exists():
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
        
        metadata["metrics"]["restarts"] += 1
        metadata["agents"]["meta"]["status"] = "restart_triggered"
        
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
    
    print("🔄 Meta-agent finished - new subagent created!")
    print("🔄 Triggering restart to load new agent...")
    
    # Create restart script
    restart_script = tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.sh',
        prefix='dynamic_restart_',
        delete=False
    )
    
    restart_script.write(f'''#!/bin/bash
# Dynamic Agent Restart Script
echo "🔄 Restarting Claude Code to load new subagent..."

# Wait for current process to exit
sleep 2

# Change to working directory
cd "{working_dir}"

# Restart Claude Code with continuation
claude --continue

echo "✅ Claude Code restarted with new subagent available!"

# Clean up
rm -f "{restart_script.name}"
''')
    
    restart_script.flush()
    restart_script.close()
    
    # Make executable
    os.chmod(restart_script.name, 0o755)
    
    print(f"🚀 Executing restart script: {restart_script.name}")
    
    # Execute restart script in background
    subprocess.Popen([restart_script.name], 
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL,
                   start_new_session=True)


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


def extract_task_info_from_session(session_dir, max_retries=10, retry_delay=2.0):
    """Extract the most recent Task completion info from session events."""
    events_file = session_dir / "session_events.json"
    
    if not events_file.exists():
        return None, None
    
    # Retry mechanism to handle race condition
    for attempt in range(max_retries):
        try:
            with open(events_file, "r") as f:
                events_data = json.load(f)
            
            # Find the most recent Task call and completion pair
            task_call_events = [
                e for e in events_data['events'] 
                if e['event_type'] == 'pre_tool_use' and 
                   e['data']['tool_name'] == 'Task'
            ]
            
            task_completion_events = [
                e for e in events_data['events'] 
                if e['event_type'] == 'post_tool_use' and 
                   e['data']['tool_name'] == 'Task'
            ]
            
            if not task_call_events or not task_completion_events:
                if attempt < max_retries - 1:
                    print(f"⏳ Task completion not found, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                    import time
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"❌ Task completion not found after {max_retries} attempts", file=sys.stderr)
                    return None, None
            
            # Get the most recent Task call to extract subagent_type
            latest_call = task_call_events[-1]
            subagent_type = latest_call['data']['tool_input'].get('subagent_type', 'unknown')
            
            # Get the most recent Task completion to extract result
            latest_completion = task_completion_events[-1]
            result = None
            
            if 'tool_response' in latest_completion['data']:
                response = latest_completion['data']['tool_response']
                if 'content' in response and response['content']:
                    result = response['content'][0]['text']
            
            return subagent_type, result
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Error extracting Task info (attempt {attempt + 1}/{max_retries}): {e}", file=sys.stderr)
                import time
                time.sleep(retry_delay)
                continue
            else:
                print(f"❌ Final error extracting Task info: {e}", file=sys.stderr)
                return None, None
    
    return None, None

def main():
    """Main subagent stop hook handler."""
    try:
        # Read input data
        input_data = json.loads(sys.stdin.read())
        
        # Add delay to ensure session file is written (race condition fix)
        import time
        time.sleep(1.0)  # 1000ms delay to handle race condition
        
        # Find session directory
        session_id = input_data.get('session_id', 'unknown')
        session_dir = find_session_directory(session_id)
        
        if session_dir:
            # WORKAROUND: Extract Task info from session events
            # This compensates for Claude Code not passing complete data to SubagentStop
            subagent_type, task_result = extract_task_info_from_session(session_dir)
            
            if subagent_type and not input_data.get('subagent_type'):
                print(f"🔍 Extracted subagent_type: {subagent_type}", file=sys.stderr)
                input_data['subagent_type'] = subagent_type
            
            if task_result and not input_data.get('result'):
                print(f"🔍 Extracted Task result from session events", file=sys.stderr)
                input_data['result'] = task_result
            
            # Log the subagent stop
            log_subagent_stop(session_dir, input_data)
            
            # Update session and check if restart needed
            needs_restart = update_session_with_subagent_stop(session_dir, input_data)
            
            subagent_type = input_data.get('subagent_type', 'unknown')
            print(f"🔄 Subagent stop logged: {subagent_type} for session: {session_id}", file=sys.stderr)
            
            # If this was meta-agent creating new agent, trigger restart
            if needs_restart and subagent_type == 'meta-agent':
                trigger_restart_for_meta_agent(input_data, session_dir)
                
        else:
            print(f"⚠️  Session directory not found for: {session_id}", file=sys.stderr)
        
        # Exit successfully
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Subagent stop hook error: {e}", file=sys.stderr)
        sys.exit(0)  # Fail gracefully


if __name__ == '__main__':
    main()