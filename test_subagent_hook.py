#!/usr/bin/env python3
"""
Test SubagentStop hook specifically
"""

import subprocess
import time
from pathlib import Path

def test_subagent_stop_hook():
    """Test if SubagentStop hook triggers"""
    
    print("🧪 Testing SubagentStop hook...")
    
    # Clean up any existing log
    log_file = Path("subagent_hook.log")
    if log_file.exists():
        log_file.unlink()
    
    print("🚀 Running task that should invoke meta-agent...")
    
    try:
        # Run a task that should trigger meta-agent
        result = subprocess.run([
            "claude", 
            "--allowedTools", "Task",
            "-p", "Use the meta-agent to analyze the task: create a simple text reverser"
        ], timeout=60, capture_output=True, text=True)
        
        print(f"Command completed with return code: {result.returncode}")
        print("Output:", result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout)
        
        if result.stderr:
            print("Errors:", result.stderr[:200] + "..." if len(result.stderr) > 200 else result.stderr)
        
        # Wait a bit for hook to potentially fire
        time.sleep(2)
        
        # Check if hook log was created
        if log_file.exists():
            print("✅ SubagentStop hook triggered!")
            print(f"Hook log: {log_file.read_text()}")
            return True
        else:
            print("❌ SubagentStop hook did not trigger")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out")
        
        # Check if hook fired anyway
        if log_file.exists():
            print("✅ Hook may have triggered despite timeout")
            print(f"Hook log: {log_file.read_text()}")
            return True
        else:
            print("❌ No evidence of hook firing")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        # Cleanup
        if log_file.exists():
            print(f"Final log content: {log_file.read_text()}")
            log_file.unlink()

if __name__ == "__main__":
    success = test_subagent_stop_hook()
    print("✅ SubagentStop hook works" if success else "❌ SubagentStop hook not working")