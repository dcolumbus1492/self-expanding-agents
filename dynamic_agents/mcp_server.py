#!/usr/bin/env python3
"""
Dynamic Tool Loader MCP Server - Python Implementation

High-level MCP server that dynamically loads and serves tools from a directory.
Tools can be added at runtime without restarting the server.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import importlib.util
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOOLS_DIR = Path(__file__).parent / "generated_tools"
TOOL_MODULES_DIR = Path(__file__).parent / "tool_modules"


@dataclass
class DynamicTool:
    """Represents a dynamically loaded tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    implementation: Optional[str] = None
    module_path: Optional[Path] = None
    last_modified: Optional[datetime] = None
    
    def to_mcp_tool(self) -> Tool:
        """Convert to MCP Tool format"""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.input_schema
        )


class ToolRegistry:
    """High-level tool registry with caching and hot-reload support"""
    
    def __init__(self, tools_dir: Path, modules_dir: Path):
        self.tools_dir = tools_dir
        self.modules_dir = modules_dir
        self.tools: Dict[str, DynamicTool] = {}
        self._last_scan = datetime.min
        
    async def scan_and_load_tools(self, force: bool = False) -> None:
        """Scan directories and load/reload tools"""
        # Ensure directories exist
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.modules_dir.mkdir(parents=True, exist_ok=True)
        
        # Load JSON-based tools
        await self._load_json_tools()
        
        # Load Python module-based tools
        await self._load_module_tools()
        
        self._last_scan = datetime.now()
        logger.info(f"Loaded {len(self.tools)} tools")
    
    async def _load_json_tools(self) -> None:
        """Load tools from JSON definitions"""
        for json_file in self.tools_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(json_file.stat().st_mtime)
                tool_name = json_file.stem
                
                # Skip if not modified
                if tool_name in self.tools and self.tools[tool_name].last_modified >= mtime:
                    continue
                
                with open(json_file, 'r') as f:
                    tool_def = json.load(f)
                
                tool = DynamicTool(
                    name=tool_def.get('name', tool_name),
                    description=tool_def.get('description', ''),
                    input_schema=tool_def.get('inputSchema', {'type': 'object', 'properties': {}}),
                    implementation=tool_def.get('implementation'),
                    last_modified=mtime
                )
                
                self.tools[tool.name] = tool
                logger.info(f"Loaded JSON tool: {tool.name}")
                
            except Exception as e:
                logger.error(f"Failed to load tool {json_file}: {e}")
    
    async def _load_module_tools(self) -> None:
        """Load tools from Python modules"""
        for py_file in self.modules_dir.glob("*.py"):
            if py_file.name.startswith('_'):
                continue
                
            try:
                mtime = datetime.fromtimestamp(py_file.stat().st_mtime)
                module_name = py_file.stem
                
                # Skip if not modified
                if module_name in self.tools and self.tools[module_name].last_modified >= mtime:
                    continue
                
                # Dynamic import
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                    # Extract tool definition
                    if hasattr(module, 'TOOL_DEFINITION'):
                        tool_def = module.TOOL_DEFINITION
                        tool = DynamicTool(
                            name=tool_def.get('name', module_name),
                            description=tool_def.get('description', ''),
                            input_schema=tool_def.get('inputSchema', {'type': 'object', 'properties': {}}),
                            module_path=py_file,
                            last_modified=mtime
                        )
                        
                        self.tools[tool.name] = tool
                        logger.info(f"Loaded Python tool: {tool.name}")
                
            except Exception as e:
                logger.error(f"Failed to load module {py_file}: {e}")
    
    def get_tool(self, name: str) -> Optional[DynamicTool]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[DynamicTool]:
        """List all available tools"""
        return list(self.tools.values())


class DynamicToolServer:
    """High-level MCP server implementation"""
    
    def __init__(self):
        self.server = Server("dynamic-tools-python")
        self.registry = ToolRegistry(TOOLS_DIR, TOOL_MODULES_DIR)
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP request handlers"""
        
        @self.server.list_tools()
        async def list_tools():
            """List all available tools"""
            # Reload tools on each request
            await self.registry.scan_and_load_tools()
            
            tools = [tool.to_mcp_tool() for tool in self.registry.list_tools()]
            return tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any):
            """Execute a tool"""
            # Reload to get latest version
            await self.registry.scan_and_load_tools()
            
            tool = self.registry.get_tool(name)
            if not tool:
                raise ValueError(f"Tool '{name}' not found")
            
            try:
                result = await self._execute_tool(tool, arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _execute_tool(self, tool: DynamicTool, arguments: Any) -> Any:
        """Execute a tool with given arguments"""
        if tool.module_path:
            # Execute Python module-based tool
            module_name = tool.module_path.stem
            if module_name in sys.modules:
                module = sys.modules[module_name]
                if hasattr(module, 'execute'):
                    return await module.execute(arguments)
            raise ValueError(f"Module {module_name} does not have execute function")
        
        elif tool.implementation:
            # Execute JSON-defined implementation (simplified)
            # In production, use a proper sandboxed execution environment
            namespace = {'args': arguments, 'result': None}
            exec(tool.implementation, namespace)
            return namespace.get('result', {'status': 'completed'})
        
        else:
            raise ValueError(f"Tool {tool.name} has no implementation")
    
    async def run(self):
        """Run the MCP server"""
        logger.info("Starting Dynamic Tool MCP Server (Python)")
        
        # Initial tool load
        await self.registry.scan_and_load_tools()
        
        # Run the server
        async with stdio_server() as streams:
            await self.server.run(
                streams[0],  # stdin
                streams[1],  # stdout
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    server = DynamicToolServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())