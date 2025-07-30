"""
Research and utilities for dynamic MCP server registration

Based on the Claude Code documentation, MCP servers can be configured through:
1. CLI commands (claude mcp add)
2. JSON configuration files (.mcp.json)
3. SDK options (--mcp-config flag)

This module explores approaches for dynamic registration.
"""

import json
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, Optional


class MCPDynamicRegistration:
    """Utilities for dynamically registering MCP servers"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.mcp_config_path = project_root / ".mcp.json"
        
    def create_mcp_config(self, servers: Dict[str, Any]) -> None:
        """Create or update .mcp.json configuration file"""
        config = {
            "mcpServers": servers
        }
        
        # Write configuration
        with open(self.mcp_config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
    def add_server_to_config(self, name: str, server_config: Dict[str, Any]) -> None:
        """Add a single server to existing configuration"""
        
        # Load existing config if it exists
        if self.mcp_config_path.exists():
            with open(self.mcp_config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {"mcpServers": {}}
        
        # Add new server
        config["mcpServers"][name] = server_config
        
        # Write back
        with open(self.mcp_config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def register_stdio_server(self, name: str, command: str, args: list = None, env: dict = None) -> Dict[str, Any]:
        """Register a stdio MCP server"""
        server_config = {
            "command": command,
            "args": args or [],
            "env": env or {}
        }
        
        self.add_server_to_config(name, server_config)
        return server_config
    
    def register_generated_mcp_server(self, name: str, server_path: Path) -> Dict[str, Any]:
        """Register a generated MCP server using Node.js"""
        
        # For macOS/Linux, run node directly
        server_config = {
            "command": "node",
            "args": [str(server_path)]
        }
        
        self.add_server_to_config(name, server_config)
        return server_config
    
    def get_allowed_tools_for_sdk(self, include_mcp_server: str) -> list:
        """Get list of allowed tools including MCP server tools"""
        
        # Base Claude Code tools
        base_tools = [
            "Task", "Read", "Write", "MultiEdit", "Edit",
            "Bash", "Grep", "Glob", "LS", "WebFetch",
            "TodoWrite", "NotebookRead", "NotebookEdit"
        ]
        
        # Add MCP server tools (format: mcp__servername__toolname)
        # We can either allow all tools from a server or specific ones
        mcp_tools = [f"mcp__{include_mcp_server}"]  # This allows all tools from the server
        
        return base_tools + mcp_tools


# Example usage for research
if __name__ == "__main__":
    # Example of how we would use this in practice
    project_root = Path.cwd()
    mcp_reg = MCPDynamicRegistration(project_root)
    
    # Example: Register a generated data processing server
    server_path = project_root / "dynamic_agents" / "generated_mcp" / "data_processor.js"
    
    # This would be called after generating the MCP server code
    config = mcp_reg.register_generated_mcp_server(
        name="data-processor",
        server_path=server_path
    )
    
    print(f"Registered MCP server config: {json.dumps(config, indent=2)}")
    
    # Get tools list for SDK
    tools = mcp_reg.get_allowed_tools_for_sdk("data-processor")
    print(f"Allowed tools for SDK: {tools}")
    
    # Note: The challenge is that Claude Code SDK needs to be restarted
    # or use --mcp-config flag to pick up new MCP servers.
    # 
    # Potential approaches:
    # 1. Pre-generate .mcp.json and use --mcp-config in SDK call
    # 2. Use subprocess to call 'claude mcp add' (but this affects global state)
    # 3. Generate all tools in a single MCP server that's pre-registered
    
    print("\nDynamic registration approaches:")
    print("1. Use .mcp.json + --mcp-config flag in SDK")
    print("2. Pre-register a 'dynamic-tools' MCP server that can load tools at runtime")
    print("3. Generate new agents that use Task tool to invoke other Claude instances with MCP config")