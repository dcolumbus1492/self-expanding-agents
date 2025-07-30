"""
Tool Generator - Creates MCP tool definitions from specifications
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import re


class MCPToolGenerator:
    """Generates MCP tool code from specifications"""
    
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.server_template = (template_dir / "mcp_server_template.js").read_text()
        
    def generate_tool_code(self, tool_spec: Dict[str, Any]) -> str:
        """Generate JavaScript code for a single MCP tool"""
        
        name = tool_spec['name']
        description = tool_spec.get('description', '')
        parameters = tool_spec.get('parameters', {})
        implementation = tool_spec.get('implementation', '')
        
        # Generate parameter schema
        param_schema = self._generate_zod_schema(parameters)
        
        # Generate parameter destructuring
        param_names = list(parameters.keys()) if parameters else []
        param_destructure = f"{{ {', '.join(param_names)} }}" if param_names else "{}"
        
        tool_code = f'''
server.tool(
  "{name}",
  "{description}",
  {param_schema},
  async ({param_destructure}) => {{
    try {{
      {implementation}
    }} catch (error) {{
      return {{
        content: [{{
          type: "text",
          text: `Error in {name}: ${{error.message}}`
        }}]
      }};
    }}
  }}
);'''
        return tool_code
    
    def _generate_zod_schema(self, parameters: Dict[str, Any]) -> str:
        """Generate Zod schema from parameter specification"""
        
        if not parameters:
            return "{}"
        
        schema_parts = []
        for param_name, param_spec in parameters.items():
            param_type = param_spec.get('type', 'string')
            param_desc = param_spec.get('description', '')
            required = param_spec.get('required', True)
            
            # Map types to Zod validators
            zod_type = {
                'string': 'z.string()',
                'number': 'z.number()',
                'boolean': 'z.boolean()',
                'array': 'z.array(z.string())',  # Default to string array
                'object': 'z.object({}).passthrough()'
            }.get(param_type, 'z.string()')
            
            # Add optional modifier if not required
            if not required:
                zod_type += '.optional()'
                
            # Add description
            if param_desc:
                zod_type += f'.describe("{param_desc}")'
                
            schema_parts.append(f'    {param_name}: {zod_type}')
        
        return "{\n" + ",\n".join(schema_parts) + "\n  }"
    
    def generate_mcp_server(self, server_spec: Dict[str, Any]) -> str:
        """Generate complete MCP server code from specification"""
        
        server_name = server_spec.get('name', 'dynamic-tools')
        server_desc = server_spec.get('description', 'Dynamically generated MCP tools')
        tools = server_spec.get('tools', [])
        helpers = server_spec.get('helpers', '')
        
        # Generate tool codes
        tool_codes = []
        for tool_spec in tools:
            tool_codes.append(self.generate_tool_code(tool_spec))
        
        # Replace placeholders in template
        server_code = self.server_template
        server_code = server_code.replace('{{SERVER_NAME}}', server_name)
        server_code = server_code.replace('{{SERVER_DESCRIPTION}}', server_desc)
        server_code = server_code.replace('// {{TOOLS_PLACEHOLDER}}', '\n'.join(tool_codes))
        server_code = server_code.replace('// {{HELPERS_PLACEHOLDER}}', helpers)
        
        # Clean up unused placeholders
        server_code = server_code.replace('// {{RESOURCES_PLACEHOLDER}}', '')
        server_code = server_code.replace('// {{PROMPTS_PLACEHOLDER}}', '')
        
        return server_code


# Example specifications for different tool types
EXAMPLE_TOOL_SPECS = {
    "data_processor": {
        "name": "data-processor",
        "description": "Tools for processing and transforming data",
        "tools": [
            {
                "name": "parse_csv",
                "description": "Parse CSV data and return as JSON",
                "parameters": {
                    "csv_data": {
                        "type": "string",
                        "description": "CSV data to parse",
                        "required": True
                    },
                    "has_headers": {
                        "type": "boolean", 
                        "description": "Whether first row contains headers",
                        "required": False
                    }
                },
                "implementation": '''
      const lines = csv_data.trim().split('\\n');
      const headers = has_headers ? lines[0].split(',') : null;
      const dataStart = has_headers ? 1 : 0;
      
      const result = [];
      for (let i = dataStart; i < lines.length; i++) {
        const values = lines[i].split(',');
        if (headers) {
          const row = {};
          headers.forEach((header, index) => {
            row[header.trim()] = values[index]?.trim() || '';
          });
          result.push(row);
        } else {
          result.push(values.map(v => v.trim()));
        }
      }
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(result, null, 2)
        }]
      };'''
            }
        ]
    },
    
    "api_client": {
        "name": "api-client",
        "description": "Dynamic API client tools",
        "tools": [
            {
                "name": "make_request",
                "description": "Make HTTP request to API endpoint",
                "parameters": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, etc.)"
                    },
                    "url": {
                        "type": "string",
                        "description": "API endpoint URL"
                    },
                    "headers": {
                        "type": "object",
                        "description": "Request headers",
                        "required": False
                    },
                    "body": {
                        "type": "object",
                        "description": "Request body for POST/PUT",
                        "required": False
                    }
                },
                "implementation": '''
      const fetch = require('node-fetch');
      
      const options = {
        method: method,
        headers: headers || {}
      };
      
      if (body && ['POST', 'PUT', 'PATCH'].includes(method)) {
        options.body = JSON.stringify(body);
        options.headers['Content-Type'] = 'application/json';
      }
      
      const response = await fetch(url, options);
      const data = await response.json();
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            status: response.status,
            data: data
          }, null, 2)
        }]
      };'''
            }
        ],
        "helpers": '''
// Helper function for authentication
function addAuthHeader(headers, token) {
  return {
    ...headers,
    'Authorization': `Bearer ${token}`
  };
}'''
    }
}


if __name__ == "__main__":
    # Example usage
    template_dir = Path(__file__).parent
    generator = MCPToolGenerator(template_dir)
    
    # Generate example data processor server
    server_code = generator.generate_mcp_server(EXAMPLE_TOOL_SPECS["data_processor"])
    
    # Save to file
    output_path = Path("generated_data_processor.js")
    output_path.write_text(server_code)
    print(f"Generated MCP server saved to: {output_path}")