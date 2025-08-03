#!/usr/bin/env python3
"""
🔄 Dynamic Agent System - Session Summary Generator
Creates comprehensive session summaries and analytics
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
import argparse


def generate_session_analytics():
    """Generate analytics across all sessions."""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return None
    
    analytics = {
        "total_sessions": 0,
        "active_sessions": 0,
        "completed_sessions": 0,
        "total_agents_created": 0,
        "total_tools_used": 0,
        "total_restarts": 0,
        "average_session_duration": 0,
        "most_active_session": None,
        "recent_sessions": []
    }
    
    session_durations = []
    sessions_data = []
    
    # Analyze each session
    for session_dir in logs_dir.glob("session_*"):
        if not session_dir.is_dir():
            continue
        
        metadata_file = session_dir / "session_metadata.json"
        if not metadata_file.exists():
            continue
        
        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            
            analytics["total_sessions"] += 1
            
            if metadata.get("status") == "active":
                analytics["active_sessions"] += 1
            elif metadata.get("status") == "completed":
                analytics["completed_sessions"] += 1
            
            # Aggregate metrics
            metrics = metadata.get("metrics", {})
            analytics["total_agents_created"] += metrics.get("agents_created", 0)
            analytics["total_tools_used"] += metrics.get("tools_used", 0)
            analytics["total_restarts"] += metrics.get("restarts", 0)
            
            # Duration analysis
            if "duration_seconds" in metadata:
                session_durations.append(metadata["duration_seconds"])
            
            # Track session data
            session_info = {
                "session_id": metadata["session_id"],
                "start_time": metadata.get("start_time"),
                "status": metadata.get("status"),
                "metrics": metrics,
                "agents_created": list(metadata.get("agents", {}).get("specialized", {}).keys())
            }
            sessions_data.append(session_info)
            
        except Exception as e:
            print(f"Error processing {session_dir}: {e}", file=sys.stderr)
            continue
    
    # Calculate averages
    if session_durations:
        analytics["average_session_duration"] = sum(session_durations) / len(session_durations)
    
    # Find most active session
    if sessions_data:
        most_active = max(sessions_data, key=lambda s: s["metrics"].get("total_interactions", 0))
        analytics["most_active_session"] = {
            "session_id": most_active["session_id"],
            "interactions": most_active["metrics"].get("total_interactions", 0)
        }
        
        # Recent sessions (last 5)
        analytics["recent_sessions"] = sorted(
            sessions_data, 
            key=lambda s: s.get("start_time", ""), 
            reverse=True
        )[:5]
    
    return analytics


def create_master_session_report():
    """Create a master report of all sessions."""
    analytics = generate_session_analytics()
    if not analytics:
        return "No session data found."
    
    # Format duration
    avg_duration = analytics["average_session_duration"]
    avg_duration_str = str(datetime.timedelta(seconds=int(avg_duration))) if avg_duration > 0 else "N/A"
    
    report = f"""# 🔄 Dynamic Agent System - Master Session Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 System Analytics

### Session Overview
- **Total Sessions**: {analytics['total_sessions']}
- **Active Sessions**: {analytics['active_sessions']} 🟢
- **Completed Sessions**: {analytics['completed_sessions']} 🔴
- **Average Duration**: {avg_duration_str}

### System Activity
- **Total Agents Created**: {analytics['total_agents_created']} 🎭
- **Total Tools Used**: {analytics['total_tools_used']} 🔧
- **Total Restarts**: {analytics['total_restarts']} 🔄

---

## 🏆 Session Highlights

### Most Active Session
"""
    
    if analytics["most_active_session"]:
        report += f"""- **Session ID**: `{analytics['most_active_session']['session_id']}`
- **Interactions**: {analytics['most_active_session']['interactions']}
"""
    else:
        report += "- No active sessions found"
    
    report += """
---

## 📝 Recent Sessions

"""
    
    if analytics["recent_sessions"]:
        for session in analytics["recent_sessions"]:
            status_icon = "🟢" if session["status"] == "active" else "🔴"
            agents_list = ", ".join(session["agents_created"]) if session["agents_created"] else "None"
            start_time = datetime.fromisoformat(session["start_time"]).strftime('%Y-%m-%d %H:%M') if session.get("start_time") else "Unknown"
            
            report += f"""### {status_icon} Session `{session['session_id']}`
- **Started**: {start_time}
- **Status**: {session['status'].title()}
- **Interactions**: {session['metrics'].get('total_interactions', 0)}
- **Tools Used**: {session['metrics'].get('tools_used', 0)}
- **Agents Created**: {agents_list}

"""
    else:
        report += "No recent sessions found."
    
    report += """---

## 🎯 System Health

"""
    
    # System health indicators
    health_indicators = []
    
    if analytics["active_sessions"] > 0:
        health_indicators.append("🟢 System is active")
    else:
        health_indicators.append("🟡 No active sessions")
    
    if analytics["total_agents_created"] > 0:
        health_indicators.append(f"🎭 {analytics['total_agents_created']} agents successfully created")
    
    if analytics["total_restarts"] > 0:
        health_indicators.append(f"🔄 {analytics['total_restarts']} successful restarts performed")
    
    for indicator in health_indicators:
        report += f"- {indicator}\n"
    
    report += f"""
---

*Generated by Dynamic Agent System v1.0*
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return report


def list_active_sessions():
    """List all active sessions with their live reports."""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        print("No logs directory found.")
        return
    
    active_sessions = []
    
    for session_dir in logs_dir.glob("session_*"):
        if not session_dir.is_dir():
            continue
        
        metadata_file = session_dir / "session_metadata.json"
        if not metadata_file.exists():
            continue
        
        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            
            if metadata.get("status") == "active":
                live_report = session_dir / "live_session_report.md"
                active_sessions.append({
                    "session_id": metadata["session_id"],
                    "start_time": metadata.get("start_time"),
                    "report_path": str(live_report) if live_report.exists() else None
                })
        except:
            continue
    
    if active_sessions:
        print("🟢 Active Sessions:")
        for session in active_sessions:
            start_time = datetime.fromisoformat(session["start_time"]).strftime('%Y-%m-%d %H:%M') if session.get("start_time") else "Unknown"
            print(f"  - {session['session_id']} (started: {start_time})")
            if session["report_path"]:
                print(f"    Report: {session['report_path']}")
    else:
        print("🔴 No active sessions found.")


def main():
    """Main session summary generator."""
    parser = argparse.ArgumentParser(description="Generate session summaries and analytics")
    parser.add_argument('--master-report', action='store_true', help='Generate master session report')
    parser.add_argument('--list-active', action='store_true', help='List active sessions')
    parser.add_argument('--output', type=str, help='Output file path for master report')
    
    args = parser.parse_args()
    
    if args.list_active:
        list_active_sessions()
        return
    
    if args.master_report:
        report = create_master_session_report()
        
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(report)
            print(f"📊 Master report saved to: {output_path}")
        else:
            # Default output location
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            output_path = logs_dir / "master_session_report.md"
            with open(output_path, 'w') as f:
                f.write(report)
            print(f"📊 Master report saved to: {output_path}")
    else:
        print("Use --master-report or --list-active")


if __name__ == '__main__':
    main()