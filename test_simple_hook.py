#!/usr/bin/env python3
"""
Test if hooks are working at all with a simple PreToolUse hook
"""

import subprocess
import tempfile
import json
from pathlib import Path

def create_simple_hook_config():
    """Create a simple hook that logs tool usage"""
    
    log_file = Path("tool_usage.log")
    if log_file.exists():
        log_file.unlink()
    
    hook_config = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"echo 'Tool used:' >> {log_file.absolute()}"
                        }
                    ]
                }
            ]
        }
    }
    
    # Write to .claude/settings.local.json
    settings_file = Path(".claude/settings.local.json")
    settings_file.write_text(json.dumps(hook_config, indent=2))
    
    print(f"✅ Created simple hook config in {settings_file}")
    print(f"🔍 Logs will go to: {log_file.absolute()}")
    
    return log_file

def test_simple_hook():
    """Test if any hooks work at all"""
    
    print("🧪 Testing basic hook functionality...")
    
    log_file = create_simple_hook_config()
    
    try:
        # Run a simple Claude command that should trigger PreToolUse
        result = subprocess.run([
            "claude", "-p", "Run the command 'echo hello world'"
        ], timeout=30, capture_output=True, text=True)
        
        print("Claude command completed")
        print(f"Return code: {result.returncode}")
        
        # Check if log file was created
        if log_file.exists():
            print("✅ Hook triggered - log file created!")
            print(f"Log contents: {log_file.read_text()}")
            return True
        else:
            print("❌ Hook not triggered - no log file found")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out")
        
        # Still check if hook worked
        if log_file.exists():
            print("✅ Hook may have triggered despite timeout")
            return True
        else:
            print("❌ No evidence of hook triggering")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        # Cleanup
        if log_file.exists():
            log_file.unlink()

if __name__ == "__main__":
    success = test_simple_hook()
    print("✅ Basic hooks work" if success else "❌ Hooks not working")