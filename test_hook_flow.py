#!/usr/bin/env python3
"""
Test Hook-Based Dynamic Agent Flow
Tests the elegant hook-based approach
"""

import subprocess
import sys
from pathlib import Path

def test_hook_based_flow():
    """Test the hook-based dynamic agent system"""
    
    print("🔄 TESTING HOOK-BASED DYNAMIC AGENT FLOW")
    print("=" * 60)
    
    # Check required files
    required_files = [
        "dynamic_agents/system_prompts/primary_agent.md",
        ".claude/agents/meta-agent.md", 
        "dynamic_agents/restart_hook.py",
        ".claude/hooks_config.json",
        "start_dynamic_system.py"
    ]
    
    print("📋 Checking required files...")
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            return False
    
    # Create test file
    test_file = Path("hook_test.txt") 
    test_content = "This is a test file for hook-based dynamic agents."
    test_file.write_text(test_content)
    print(f"✅ Created test file: {test_file}")
    
    # Test task that should trigger meta-agent and hook
    task = f"Create a specialized agent that converts text to leetspeak (1337 speak) and apply it to {test_file}"
    
    print(f"\n🎯 Test task: {task}")
    print("\nExpected flow:")
    print("1. Primary agent delegates to meta-agent")
    print("2. Meta-agent creates leetspeak-converter agent")
    print("3. SubagentStop hook triggers automatic restart")
    print("4. System continues with new agent available")
    
    print(f"\n🚀 Starting dynamic system with task...")
    
    try:
        # Use the launcher script with restricted permissions
        result = subprocess.run([
            "python3", "start_dynamic_system.py", task
        ], timeout=45, text=True, capture_output=True)
        
        print("\n📋 RESULT:")
        print(result.stdout)
        
        if result.stderr:
            print("\n⚠️  Errors:")
            print(result.stderr)
        
        # Check if new agent was created
        agents_dir = Path(".claude/agents")
        leetspeak_agents = [f for f in agents_dir.glob("*.md") if "leet" in f.name.lower()]
        
        if leetspeak_agents:
            print(f"\n✅ SUCCESS: Leetspeak agent created: {leetspeak_agents[0].name}")
        else:
            print("\n⚠️  Leetspeak agent not found")
        
        return len(leetspeak_agents) > 0
        
    except subprocess.TimeoutExpired:
        print("\n⏰ Test timed out")
        print("This may indicate the hook restart occurred")
        
        # Check if agent was created anyway
        agents_dir = Path(".claude/agents")
        leetspeak_agents = [f for f in agents_dir.glob("*.md") if "leet" in f.name.lower()]
        
        if leetspeak_agents:
            print(f"✅ Agent created despite timeout: {leetspeak_agents[0].name}")
            return True
        
        return False
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False
        
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
            print("🧹 Cleaned up test file")

def test_launcher_basic():
    """Test the launcher basic functionality"""
    print("\n🧪 Testing launcher basic functionality...")
    
    try:
        result = subprocess.run([
            "python3", "start_dynamic_system.py", "--help"
        ], timeout=10, text=True, capture_output=True)
        
        if result.returncode == 0:
            print("✅ Launcher works correctly")
            return True
        else:
            print(f"❌ Launcher failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Launcher test failed: {e}")
        return False

def main():
    """Run hook-based flow tests"""
    
    print("🔄 HOOK-BASED DYNAMIC AGENT SYSTEM TEST")
    print("=" * 60)
    print("This tests the elegant hook-based approach that:")
    print("• Uses primary agent with tool restrictions")
    print("• Automatically triggers restart via SubagentStop hook")
    print("• Preserves session with --continue")
    print("• Makes new agents immediately available")
    
    # Run tests
    tests = [
        ("Launcher Basic", test_launcher_basic),
        ("Hook-Based Flow", test_hook_based_flow)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 HOOK-BASED FLOW TEST RESULTS:")
    print("-" * 40)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n🎯 {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🔥 HOOK-BASED DYNAMIC AGENT SYSTEM: READY! 🔥")
        print("Run: python3 start_dynamic_system.py --interactive")
    else:
        print("\n⚠️  Some issues detected")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)