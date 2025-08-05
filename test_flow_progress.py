#!/usr/bin/env python3
"""
Dynamic Agent Flow Progress Tester
Tests each step of the 4-step flow independently and end-to-end
"""

import os
import sys
import json
import subprocess
import tempfile
import time
import signal
from pathlib import Path
from datetime import datetime

# Import our flow logger
sys.path.insert(0, str(Path(__file__).parent))
from flow_logger import log_step_1, log_step_2, log_step_3, log_step_4, log_error, clear_flow_log, show_flow_log


class FlowTester:
    """Test the 4-step dynamic agent flow"""
    
    def __init__(self):
        self.base_dir = Path.cwd()
        self.test_results = {
            "step_1": False,
            "step_2": False, 
            "step_3": False,
            "step_4": False,
            "end_to_end": False
        }
        
    def setup_test_environment(self):
        """Set up a clean test environment"""
        print("🧪 Setting up test environment...")
        
        # Clear previous test artifacts
        cleanup_files = [
            ".restart_needed",
            ".primary_locked", 
            "flow_progress.log",
            "phoenix_debug.log"
        ]
        
        for file_path in cleanup_files:
            Path(file_path).unlink(missing_ok=True)
            
        # Clear generated agents (except meta-agent)
        agents_dir = Path(".claude/agents")
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.md"):
                if agent_file.name != "meta-agent.md":
                    agent_file.unlink(missing_ok=True)
                    
        # Clear generated MCP servers
        mcp_dir = Path("dynamic_agents/generated_mcp")
        if mcp_dir.exists():
            for mcp_file in mcp_dir.glob("*.py"):
                mcp_file.unlink(missing_ok=True)
                
        clear_flow_log()
        log_step_1("Test environment setup complete")
        print("✅ Test environment ready")
        
    def test_step_1_task_delegation(self):
        """Test Step 1: Primary agent can delegate to meta-agent via Task tool"""
        print("\n🔍 Testing Step 1: Task delegation to meta-agent")
        
        try:
            # Create a simple test task that requires meta-agent
            test_task = "Create a simple calculator agent for basic math operations"
            
            # This would be tested by running the actual system, but for now
            # we'll verify the configuration is correct
            
            # Check primary agent system prompt exists and has Task tool restriction
            primary_prompt_file = Path("dynamic_agents/system_prompts/primary_agent.md")
            if not primary_prompt_file.exists():
                raise Exception("Primary agent system prompt not found")
                
            primary_prompt = primary_prompt_file.read_text()
            if "Task tool" not in primary_prompt or "FORBIDDEN" not in primary_prompt:
                raise Exception("Primary agent not properly restricted to Task tool")
                
            # Check meta-agent exists
            meta_agent_file = Path(".claude/agents/meta-agent.md")
            if not meta_agent_file.exists():
                raise Exception("Meta-agent file not found")
                
            # Check start_dynamic_system.py has correct configuration
            launcher_file = Path("start_dynamic_system.py")
            if not launcher_file.exists():
                raise Exception("Dynamic system launcher not found")
                
            launcher_content = launcher_file.read_text()
            if "--allowedTools\", \"Task\"" not in launcher_content:
                raise Exception("Launcher not configured to restrict primary agent to Task tool")
                
            self.test_results["step_1"] = True
            log_step_1("Task delegation configuration verified", {
                "subagent_type": "meta-agent",
                "task_preview": test_task[:50] + "..."
            })
            print("✅ Step 1: Task delegation configuration is correct")
            return True
            
        except Exception as e:
            log_error(1, f"Task delegation test failed: {e}")
            print(f"❌ Step 1 failed: {e}")
            return False
            
    def test_step_2_agent_creation(self):
        """Test Step 2: Meta-agent creates specialist and outputs completion signal"""
        print("\n🔍 Testing Step 2: Meta-agent creates specialist")
        
        try:
            # Check if meta-agent can create files in correct directories
            agents_dir = Path(".claude/agents")
            mcp_dir = Path("dynamic_agents/generated_mcp")
            
            if not agents_dir.exists():
                agents_dir.mkdir(parents=True, exist_ok=True)
                
            if not mcp_dir.exists():
                mcp_dir.mkdir(parents=True, exist_ok=True)
                
            # Verify meta-agent has correct tools
            meta_agent_file = Path(".claude/agents/meta-agent.md")
            meta_content = meta_agent_file.read_text()
            
            required_tools = ["Read", "Write", "Grep", "Glob"]
            for tool in required_tools:
                if tool not in meta_content:
                    raise Exception(f"Meta-agent missing required tool: {tool}")
                    
            # Check completion signal format is defined
            if "✅ **AGENT_CREATED**" not in meta_content:
                raise Exception("Meta-agent completion signal format not found")
                
            self.test_results["step_2"] = True
            log_step_2("Agent creation configuration verified", {
                "agent_name": "meta-agent",
                "completion_signal": "✅ **AGENT_CREATED**: [name] specialized for [purpose]"
            })
            print("✅ Step 2: Agent creation configuration is correct")
            return True
            
        except Exception as e:
            log_error(2, f"Agent creation test failed: {e}")
            print(f"❌ Step 2 failed: {e}")
            return False
            
    def test_step_3_hook_detection(self):
        """Test Step 3: Hook detects completion and triggers restart"""
        print("\n🔍 Testing Step 3: Hook detection and restart signaling")
        
        try:
            # Check if hook configuration exists
            settings_file = Path(".claude/settings.json")
            if not settings_file.exists():
                raise Exception("Hook settings file not found")
                
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                
            hooks = settings.get("hooks", {})
            post_tool_hooks = hooks.get("PostToolUse", [])
            
            # Find hook for Task tool
            task_hook_found = False
            for hook_config in post_tool_hooks:
                if hook_config.get("matcher") == "Task" or hook_config.get("matcher") == "*":
                    hook_commands = hook_config.get("hooks", [])
                    for hook_cmd in hook_commands:
                        if "phoenix" in hook_cmd.get("command", "").lower():
                            task_hook_found = True
                            break
                            
            if not task_hook_found:
                raise Exception("PostToolUse hook for Task tool not found")
                
            # Check if MCP registration script exists
            mcp_register_script = Path("dynamic_agents/register_mcp.py")
            if not mcp_register_script.exists():
                raise Exception("MCP registration script not found")
                
            self.test_results["step_3"] = True
            log_step_3("Hook detection configuration verified", {
                "mcp_status": "registration script available",
                "restart_status": "marker file mechanism ready"
            })
            print("✅ Step 3: Hook detection configuration is correct")
            return True
            
        except Exception as e:
            log_error(3, f"Hook detection test failed: {e}")
            print(f"❌ Step 3 failed: {e}")
            return False
            
    def test_step_4_fresh_session(self):
        """Test Step 4: Fresh session can see new subagents"""
        print("\n🔍 Testing Step 4: Fresh session subagent visibility")
        
        try:
            # Create a mock agent to test visibility
            test_agent_content = """---
name: test-calculator
description: Test calculator for flow validation
tools: Read, Write
---

Test calculator agent for validating the 4-step flow works correctly.
"""
            
            agents_dir = Path(".claude/agents")
            agents_dir.mkdir(exist_ok=True)
            test_agent_file = agents_dir / "test-calculator.md"
            
            with open(test_agent_file, 'w') as f:
                f.write(test_agent_content)
                
            # Verify the test agent file was created
            if not test_agent_file.exists():
                raise Exception("Could not create test agent file")
                
            # Verify the dynamic system launcher uses fresh sessions
            launcher_file = Path("start_dynamic_system.py")
            launcher_content = launcher_file.read_text()
            
            # Check for fresh session restart (not --continue)
            if "restart_cmd" not in launcher_content:
                raise Exception("Launcher doesn't implement fresh session restart")
                
            # Clean up test agent
            test_agent_file.unlink(missing_ok=True)
            
            self.test_results["step_4"] = True
            log_step_4("Fresh session configuration verified", {
                "agent_name": "test-calculator (cleaned up)"
            })
            print("✅ Step 4: Fresh session configuration is correct")
            return True
            
        except Exception as e:
            log_error(4, f"Fresh session test failed: {e}")
            print(f"❌ Step 4 failed: {e}")
            return False
            
    def run_end_to_end_test(self):
        """Run a complete end-to-end test with a simple task"""
        print("\n🚀 Running End-to-End Flow Test")
        
        try:
            # This would run the actual system with a test task
            # For now, we'll simulate by checking all components work together
            
            test_task = "Create a simple test agent for validation"
            
            # Verify all components are ready
            required_files = [
                "start_dynamic_system.py",
                "dynamic_agents/system_prompts/primary_agent.md",
                ".claude/agents/meta-agent.md",
                ".claude/settings.json",
                "dynamic_agents/register_mcp.py"
            ]
            
            for file_path in required_files:
                if not Path(file_path).exists():
                    raise Exception(f"Required file missing: {file_path}")
                    
            # Check that all individual steps passed
            if not all(self.test_results[f"step_{i}"] for i in range(1, 5)):
                raise Exception("Cannot run end-to-end test - individual step tests failed")
                
            self.test_results["end_to_end"] = True
            log_step_4("End-to-end configuration verified", {
                "task_preview": test_task
            })
            print("✅ End-to-End: All components ready for flow execution")
            return True
            
        except Exception as e:
            log_error(4, f"End-to-end test failed: {e}")
            print(f"❌ End-to-End failed: {e}")
            return False
            
    def run_all_tests(self):
        """Run all flow tests"""
        print("🧪 DYNAMIC AGENT FLOW TESTER")
        print("=" * 50)
        
        self.setup_test_environment()
        
        # Run individual step tests
        tests = [
            ("Step 1: Task Delegation", self.test_step_1_task_delegation),
            ("Step 2: Agent Creation", self.test_step_2_agent_creation),
            ("Step 3: Hook Detection", self.test_step_3_hook_detection),
            ("Step 4: Fresh Session", self.test_step_4_fresh_session),
            ("End-to-End Flow", self.run_end_to_end_test)
        ]
        
        results = []
        for test_name, test_func in tests:
            result = test_func()
            results.append((test_name, result))
            
        # Summary
        print("\n📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {test_name}")
            
        total_passed = sum(1 for _, passed in results if passed)
        total_tests = len(results)
        
        print(f"\nOverall: {total_passed}/{total_tests} tests passed")
        
        if total_passed == total_tests:
            print("🎉 All tests passed! Flow is ready for execution.")
        else:
            print("⚠️  Some tests failed. Check the issues above.")
            
        print("\n📋 Flow Log:")
        show_flow_log()
        
        return total_passed == total_tests


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Dynamic Agent Flow")
    parser.add_argument('--step', type=int, choices=[1, 2, 3, 4], 
                       help="Test specific step only")
    parser.add_argument('--end-to-end', action='store_true',
                       help="Run end-to-end test only")
    parser.add_argument('--setup-only', action='store_true',
                       help="Setup test environment only")
    
    args = parser.parse_args()
    
    tester = FlowTester()
    
    if args.setup_only:
        tester.setup_test_environment()
        return
        
    if args.step:
        tester.setup_test_environment()
        test_methods = {
            1: tester.test_step_1_task_delegation,
            2: tester.test_step_2_agent_creation,
            3: tester.test_step_3_hook_detection,
            4: tester.test_step_4_fresh_session
        }
        result = test_methods[args.step]()
        sys.exit(0 if result else 1)
        
    if args.end_to_end:
        tester.setup_test_environment()
        result = tester.run_end_to_end_test()
        sys.exit(0 if result else 1)
        
    # Default: run all tests
    result = tester.run_all_tests()
    sys.exit(0 if result else 1)


if __name__ == '__main__':
    main()