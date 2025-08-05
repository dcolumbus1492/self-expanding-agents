#!/usr/bin/env python3

import asyncio
import json
import sys
import math
import re
from typing import Any, Dict

class SimpleMCPServer:
    def __init__(self):
        self.tools = {
            "calculate": {
                "name": "calculate",
                "description": "Evaluate mathematical expressions including basic arithmetic, trigonometric functions, logarithms, and constants like pi and e",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string", 
                            "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4', 'sin(pi/2)', 'sqrt(16)', 'log(10)')"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "calculator",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0", 
                "id": request.get("id"),
                "result": {"tools": list(self.tools.values())}
            }
        
        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            try:
                result = await self.execute_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [{"type": "text", "text": str(result)}]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32000, "message": str(e)}
                }

    def safe_eval(self, expression: str):
        """Safely evaluate mathematical expressions"""
        # Remove whitespace
        expression = expression.strip()
        
        # Replace common mathematical functions and constants
        replacements = {
            'pi': str(math.pi),
            'e': str(math.e),
            'sin': 'math.sin',
            'cos': 'math.cos',
            'tan': 'math.tan',
            'asin': 'math.asin',
            'acos': 'math.acos',
            'atan': 'math.atan',
            'sinh': 'math.sinh',
            'cosh': 'math.cosh',
            'tanh': 'math.tanh',
            'log': 'math.log',
            'log10': 'math.log10',
            'log2': 'math.log2',
            'sqrt': 'math.sqrt',
            'pow': 'math.pow',
            'exp': 'math.exp',
            'abs': 'abs',
            'ceil': 'math.ceil',
            'floor': 'math.floor',
            'round': 'round',
            'factorial': 'math.factorial',
            'gcd': 'math.gcd',
            'degrees': 'math.degrees',
            'radians': 'math.radians'
        }
        
        # Apply replacements with word boundaries
        for func, replacement in replacements.items():
            pattern = r'\b' + func + r'\b'
            expression = re.sub(pattern, replacement, expression)
        
        # Only allow safe characters and operations
        allowed_chars = set('0123456789+-*/().eE mathsincotaglqrpwxbfcdru_')
        if not all(c in allowed_chars for c in expression):
            raise ValueError("Expression contains invalid characters")
        
        # Evaluate the expression
        try:
            # Create a restricted environment for evaluation
            safe_dict = {
                "__builtins__": {},
                "math": math,
                "abs": abs,
                "round": round
            }
            return eval(expression, safe_dict)
        except Exception as e:
            raise ValueError(f"Error evaluating expression: {str(e)}")

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]):
        if tool_name == "calculate":
            expression = arguments.get('expression', '')
            if not expression:
                raise ValueError("Expression cannot be empty")
            
            try:
                result = self.safe_eval(expression)
                return f"Result: {result}"
            except Exception as e:
                raise ValueError(f"Calculation error: {str(e)}")
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def run(self):
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line.strip())
                response = await self.handle_request(request)
                print(json.dumps(response), flush=True)
            except (EOFError, KeyboardInterrupt, json.JSONDecodeError):
                break

if __name__ == "__main__":
    server = SimpleMCPServer()
    asyncio.run(server.run())