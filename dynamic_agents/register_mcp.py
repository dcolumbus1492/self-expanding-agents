#!/usr/bin/env python3
"""Script to auto-discover and register MCP servers from dynamic_agents/generated_mcp/"""

import subprocess
import sys
from pathlib import Path

def register_mcp_servers():
    """Auto-discover and register MCP servers from dynamic_agents/generated_mcp/"""
    
    mcp_dir = Path("dynamic_agents/generated_mcp")
    if not mcp_dir.exists():
        print("❌ No MCP servers directory found: dynamic_agents/generated_mcp/")
        return False
    
    # Find all Python files (potential MCP servers)
    server_files = list(mcp_dir.glob("*.py"))
    if not server_files:
        print("❌ No Python MCP servers found in dynamic_agents/generated_mcp/")
        return False
    
    # Filter out __init__.py and other non-server files
    server_files = [f for f in server_files if not f.name.startswith('__')]
    
    if not server_files:
        print("❌ No valid MCP server files found")
        return False
        
    print(f"🔌 Auto-discovering and registering {len(server_files)} MCP servers...")
    
    success_count = 0
    
    for server_file in server_files:
        server_name = server_file.stem.replace('_', '-')  # Convert underscores to hyphens
        server_path = str(server_file.absolute())
        
        # Build claude mcp add command (same pattern that worked before)
        cmd = ['claude', 'mcp', 'add', server_name, '--', 'python', server_path]
        
        print(f"  Registering: {server_name} from {server_file.name}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✅ {server_name} registered successfully")
            success_count += 1
        else:
            error_msg = result.stderr.strip()
            if "already exists" in error_msg:
                print(f"  ℹ️  {server_name} already registered")
                success_count += 1
            else:
                print(f"  ❌ Failed to register {server_name}: {error_msg}")
                # Don't fail the whole process if one server fails
    
    print(f"\n🎉 {success_count}/{len(server_files)} servers registered successfully")
    return success_count > 0

def list_registered_servers():
    """List currently registered MCP servers"""
    print("\n📋 Currently registered MCP servers:")
    result = subprocess.run(['claude', 'mcp', 'list'], capture_output=True, text=True)
    print(result.stdout)

if __name__ == "__main__":
    print("🔧 MCP Server Registration Script")
    print("=" * 40)
    
    success = register_mcp_servers()
    
    if success:
        list_registered_servers()
        sys.exit(0)
    else:
        sys.exit(1)