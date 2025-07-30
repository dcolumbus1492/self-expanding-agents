#!/usr/bin/env python3
"""
MCP server for leetspeak text conversion.
Provides tools to convert regular text to leetspeak (1337 speak).
"""

import asyncio
import json
from typing import Any, Sequence
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio


server = Server("leetspeak")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available leetspeak tools."""
    return [
        types.Tool(
            name="convert_to_leetspeak",
            description="Convert text to leetspeak (1337 speak) by replacing letters with numbers/symbols",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to convert to leetspeak"
                    }
                },
                "required": ["text"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    """Handle tool calls for leetspeak conversion."""
    if name != "convert_to_leetspeak":
        raise ValueError(f"Unknown tool: {name}")
    
    if not arguments or "text" not in arguments:
        raise ValueError("Missing required parameter: text")
    
    text = arguments["text"]
    
    # Leetspeak conversion mappings
    leetspeak_map = {
        'a': '4', 'A': '4',
        'e': '3', 'E': '3',
        'l': '1', 'L': '1',
        'o': '0', 'O': '0',
        's': '5', 'S': '5',
        't': '7', 'T': '7',
        'i': '!', 'I': '!',
        'g': '9', 'G': '9',
        'b': '8', 'B': '8'
    }
    
    # Convert text to leetspeak
    converted_text = ""
    for char in text:
        converted_text += leetspeak_map.get(char, char)
    
    return [
        types.TextContent(
            type="text",
            text=f"Converted to leetspeak: {converted_text}"
        )
    ]


async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="leetspeak",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())