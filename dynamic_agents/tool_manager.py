"""
High-level Tool Management System

Provides a comprehensive interface for creating, managing, and deploying MCP tools.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import tempfile
import subprocess
import sys
import logging
from abc import ABC, abstractmethod
import ast

logger = logging.getLogger(__name__)


@dataclass
class ToolSpecification:
    """High-level tool specification"""
    name: str
    description: str
    category: str = "general"
    version: str = "1.0.0"
    author: str = "dynamic-agent"
    parameters: Dict[str, Any] = None
    dependencies: List[str] = None
    implementation_type: str = "python"  # python, javascript, external
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.dependencies is None:
            self.dependencies = []
    
    def to_input_schema(self) -> Dict[str, Any]:
        """Convert parameters to JSON Schema format"""
        properties = {}
        required = []
        
        for param_name, param_info in self.parameters.items():
            if isinstance(param_info, dict):
                properties[param_name] = param_info
                if param_info.get('required', False):
                    required.append(param_name)
            else:
                # Simple type specification
                properties[param_name] = {"type": param_info}
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }


class ToolImplementation(ABC):
    """Abstract base for tool implementations"""
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        """Execute the tool with given arguments"""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate the implementation"""
        pass


class PythonToolBuilder:
    """Builds Python-based tools with high-level abstractions"""
    
    def __init__(self, spec: ToolSpecification):
        self.spec = spec
        self.template = '''"""
{description}

Auto-generated tool module
"""

TOOL_DEFINITION = {{
    "name": "{name}",
    "description": "{description}",
    "inputSchema": {input_schema}
}}


async def execute(arguments: dict) -> dict:
    """Execute the {name} tool"""
    {implementation}
'''
    
    def build_from_function(self, func_code: str) -> str:
        """Build tool module from function code"""
        # Parse the function to ensure it's valid Python
        try:
            ast.parse(func_code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python code: {e}")
        
        # Indent the implementation
        implementation = '\n    '.join(func_code.strip().split('\n'))
        
        return self.template.format(
            name=self.spec.name,
            description=self.spec.description,
            input_schema=json.dumps(self.spec.to_input_schema(), indent=4),
            implementation=implementation
        )
    
    def build_from_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Build tool from a predefined template"""
        templates = {
            "file_processor": self._file_processor_template,
            "api_client": self._api_client_template,
            "data_transformer": self._data_transformer_template,
        }
        
        if template_name not in templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        return templates[template_name](context)
    
    def _file_processor_template(self, context: Dict[str, Any]) -> str:
        """Template for file processing tools"""
        implementation = f'''
    from pathlib import Path
    import json
    
    filepath = Path(arguments.get('filepath', ''))
    operation = arguments.get('operation', 'read')
    
    if not filepath.exists():
        return {{"error": f"File not found: {{filepath}}"}}
    
    try:
        if operation == 'read':
            with open(filepath, 'r') as f:
                content = f.read()
            return {{"content": content}}
        elif operation == 'process':
            # Custom processing logic
            {context.get('processing_logic', 'pass')}
            return {{"status": "processed"}}
    except Exception as e:
        return {{"error": str(e)}}
'''
        
        return self.build_from_function(implementation)
    
    def _api_client_template(self, context: Dict[str, Any]) -> str:
        """Template for API client tools"""
        implementation = f'''
    import aiohttp
    import json
    
    url = arguments.get('url', '{context.get('base_url', '')}')
    method = arguments.get('method', 'GET')
    data = arguments.get('data')
    headers = arguments.get('headers', {{}})
    
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, json=data, headers=headers) as response:
            result = await response.json()
            return {{
                "status_code": response.status,
                "data": result
            }}
'''
        
        return self.build_from_function(implementation)
    
    def _data_transformer_template(self, context: Dict[str, Any]) -> str:
        """Template for data transformation tools"""
        implementation = f'''
    import json
    from typing import Any, Dict, List
    
    data = arguments.get('data')
    transformation = arguments.get('transformation', 'none')
    
    if transformation == 'flatten':
        # Flatten nested structure
        def flatten(d, parent_key='', sep='_'):
            items = []
            for k, v in d.items():
                new_key = f"{{parent_key}}{{sep}}{{k}}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)
        
        result = flatten(data) if isinstance(data, dict) else data
    elif transformation == 'aggregate':
        # Aggregate list data
        {context.get('aggregation_logic', 'result = data')}
    else:
        result = data
    
    return {{"result": result}}
'''
        
        return self.build_from_function(implementation)


class ToolManager:
    """High-level tool management interface"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent
        self.tools_dir = self.base_dir / "generated_tools"
        self.modules_dir = self.base_dir / "tool_modules"
        self.tools_dir.mkdir(exist_ok=True)
        self.modules_dir.mkdir(exist_ok=True)
        
    def create_tool(self, spec: ToolSpecification, implementation: Union[str, Dict[str, Any]]) -> Path:
        """Create a new tool with the given specification"""
        if spec.implementation_type == "python":
            return self._create_python_tool(spec, implementation)
        elif spec.implementation_type == "json":
            return self._create_json_tool(spec, implementation)
        else:
            raise ValueError(f"Unsupported implementation type: {spec.implementation_type}")
    
    def _create_python_tool(self, spec: ToolSpecification, implementation: Union[str, Dict[str, Any]]) -> Path:
        """Create a Python-based tool"""
        builder = PythonToolBuilder(spec)
        
        if isinstance(implementation, str):
            # Direct function code
            module_content = builder.build_from_function(implementation)
        elif isinstance(implementation, dict):
            # Template-based
            template_name = implementation.get('template')
            context = implementation.get('context', {})
            module_content = builder.build_from_template(template_name, context)
        else:
            raise ValueError("Invalid implementation format")
        
        # Save the module
        module_path = self.modules_dir / f"{spec.name}.py"
        with open(module_path, 'w') as f:
            f.write(module_content)
        
        logger.info(f"Created Python tool: {spec.name} at {module_path}")
        return module_path
    
    def _create_json_tool(self, spec: ToolSpecification, implementation: str) -> Path:
        """Create a JSON-based tool"""
        tool_def = {
            "name": spec.name,
            "description": spec.description,
            "inputSchema": spec.to_input_schema(),
            "implementation": implementation,
            "metadata": {
                "version": spec.version,
                "author": spec.author,
                "category": spec.category,
                "created": datetime.now().isoformat()
            }
        }
        
        tool_path = self.tools_dir / f"{spec.name}.json"
        with open(tool_path, 'w') as f:
            json.dump(tool_def, f, indent=2)
        
        logger.info(f"Created JSON tool: {spec.name} at {tool_path}")
        return tool_path
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        tools = []
        
        # List JSON tools
        for json_file in self.tools_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    tool_def = json.load(f)
                tools.append({
                    "name": tool_def.get('name', json_file.stem),
                    "type": "json",
                    "path": str(json_file),
                    "description": tool_def.get('description', ''),
                    "metadata": tool_def.get('metadata', {})
                })
            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")
        
        # List Python tools
        for py_file in self.modules_dir.glob("*.py"):
            if py_file.name.startswith('_'):
                continue
            tools.append({
                "name": py_file.stem,
                "type": "python",
                "path": str(py_file),
                "description": f"Python module: {py_file.stem}"
            })
        
        return tools
    
    def remove_tool(self, name: str) -> bool:
        """Remove a tool"""
        removed = False
        
        # Check JSON tools
        json_path = self.tools_dir / f"{name}.json"
        if json_path.exists():
            json_path.unlink()
            removed = True
        
        # Check Python tools
        py_path = self.modules_dir / f"{name}.py"
        if py_path.exists():
            py_path.unlink()
            removed = True
        
        return removed
    
    def update_tool(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update an existing tool"""
        # Try JSON tool first
        json_path = self.tools_dir / f"{name}.json"
        if json_path.exists():
            with open(json_path, 'r') as f:
                tool_def = json.load(f)
            
            # Update fields
            for key, value in updates.items():
                if key in tool_def:
                    tool_def[key] = value
            
            # Update metadata
            if 'metadata' not in tool_def:
                tool_def['metadata'] = {}
            tool_def['metadata']['updated'] = datetime.now().isoformat()
            
            with open(json_path, 'w') as f:
                json.dump(tool_def, f, indent=2)
            
            return True
        
        return False


# CLI Interface
def main():
    """Command-line interface for tool management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dynamic Tool Manager")
    subparsers = parser.add_subparsers(dest='command')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new tool')
    create_parser.add_argument('name', help='Tool name')
    create_parser.add_argument('--description', required=True, help='Tool description')
    create_parser.add_argument('--type', choices=['python', 'json'], default='python')
    create_parser.add_argument('--template', help='Use a template')
    create_parser.add_argument('--file', help='Implementation file')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all tools')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a tool')
    remove_parser.add_argument('name', help='Tool name')
    
    args = parser.parse_args()
    
    manager = ToolManager()
    
    if args.command == 'create':
        spec = ToolSpecification(
            name=args.name,
            description=args.description,
            implementation_type=args.type
        )
        
        if args.file:
            with open(args.file, 'r') as f:
                implementation = f.read()
        elif args.template:
            implementation = {'template': args.template, 'context': {}}
        else:
            implementation = "return {'result': 'Not implemented'}"
        
        path = manager.create_tool(spec, implementation)
        print(f"Created tool: {path}")
    
    elif args.command == 'list':
        tools = manager.list_tools()
        for tool in tools:
            print(f"- {tool['name']} ({tool['type']}): {tool['description']}")
    
    elif args.command == 'remove':
        if manager.remove_tool(args.name):
            print(f"Removed tool: {args.name}")
        else:
            print(f"Tool not found: {args.name}")


if __name__ == "__main__":
    main()