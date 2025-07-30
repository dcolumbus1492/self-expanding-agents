#!/usr/bin/env python3
"""Simple test to verify the SDK works with a basic prompt"""

import os
import asyncio
from claude_code_sdk import query, ClaudeCodeOptions

# Set environment variables
os.environ["CLAUDE_CODE_USE_BEDROCK"] = "1"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["ANTHROPIC_MODEL"] = "us.anthropic.claude-opus-4-20250514-v1:0"

async def main():
    options = ClaudeCodeOptions(
        max_turns=3,
        system_prompt="You are a helpful assistant."
    )
    
    # Use a very simple prompt first
    prompt = "Hello, please respond with 'Hello! I am working.'"
    
    print(f"Testing with simple prompt: {prompt}")
    
    try:
        messages = []
        async for message in query(prompt=prompt, options=options):
            messages.append(message)
            if hasattr(message, 'type'):
                print(f"Received message type: {message.type}")
        
        print(f"Success! Received {len(messages)} messages")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())