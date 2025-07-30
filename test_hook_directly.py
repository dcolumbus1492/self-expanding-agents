#!/usr/bin/env python3
"""
Test the restart hook directly
"""

import json
import subprocess
import sys
from pathlib import Path

def test_hook_script():
    """Test the restart hook script with mock data"""
    
    # Mock subagent stop data for meta-agent
    mock_data = {
        "subagent_type": "meta-agent",
        "result": "Successfully created specialized agent for leetspeak conversion",
        "session_id": "test-session-123"
    }
    
    print("🧪 Testing restart hook with mock data...")
    print(f"Mock data: {json.dumps(mock_data, indent=2)}")
    
    hook_script = Path("dynamic_agents/restart_hook.py")
    if not hook_script.exists():
        print("❌ Hook script not found")
        return False
    
    try:
        # Run hook script with mock data
        process = subprocess.Popen([
            "python3", str(hook_script)
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        stdout, stderr = process.communicate(input=json.dumps(mock_data))
        
        print(f"Return code: {process.returncode}")
        print(f"Stdout: {stdout}")
        if stderr:
            print(f"Stderr: {stderr}")
        
        return process.returncode == 0
        
    except Exception as e:
        print(f"❌ Hook test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_hook_script()
    print("✅ Hook test passed" if success else "❌ Hook test failed")
    sys.exit(0 if success else 1)