#!/usr/bin/env python3
"""
Dynamic Agent System - Main Entry Point
Orchestrates dynamic agent and tool generation using Claude Code SDK
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Check if claude_code_sdk is available
try:
    from claude_code_sdk import query, ClaudeCodeOptions, Message
except ImportError:
    print("Error: claude_code_sdk not installed. Please run: pip install claude-code-sdk")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DynamicAgentOrchestrator:
    """Main orchestrator for dynamic agent system"""
    
    def __init__(self, working_dir: Optional[Path] = None):
        self.working_dir = working_dir or Path.cwd()
        self.system_prompts_dir = Path(__file__).parent / "system_prompts"
        self.generated_agents_dir = self.working_dir / ".claude" / "agents"
        self.generated_mcp_dir = self.working_dir / "dynamic_agents" / "generated_mcp"
        
        # Ensure directories exist
        self.generated_agents_dir.mkdir(parents=True, exist_ok=True)
        self.generated_mcp_dir.mkdir(parents=True, exist_ok=True)
        
        # Load main orchestrator prompt
        self.main_prompt = self._load_system_prompt("main_orchestrator.md")
        
    def _load_system_prompt(self, filename: str) -> str:
        """Load a system prompt from file"""
        prompt_path = self.system_prompts_dir / filename
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        else:
            logger.warning(f"System prompt file not found: {prompt_path}")
            return ""
    
    async def process_request(self, user_prompt: str, options: Optional[ClaudeCodeOptions] = None) -> List[Message]:
        """Process a user request through the dynamic agent system"""
        
        # Clean up the prompt - remove newlines and extra spaces that might cause issues
        user_prompt = ' '.join(user_prompt.split())
        
        # Set default options if not provided
        if options is None:
            options = ClaudeCodeOptions(
                max_turns=20,  # Increased for multi-agent workflows
                system_prompt=self.main_prompt,
                cwd=str(self.working_dir),
                allowed_tools=["Task"],  # ONLY Task tool - must delegate everything
            )
        else:
            # Append our system prompt to any existing one
            if options.system_prompt:
                options.system_prompt = f"{options.system_prompt}\n\n{self.main_prompt}"
            else:
                options.system_prompt = self.main_prompt
        
        logger.info(f"Processing request: {user_prompt[:100]}...")
        
        messages: List[Message] = []
        
        try:
            # Execute the main orchestrator
            async for message in query(prompt=user_prompt, options=options):
                messages.append(message)
                
                # Log message types for debugging
                if hasattr(message, 'type'):
                    logger.debug(f"Received message type: {message.type}")
                    
                    # Handle specific message types if needed
                    if message.type == 'assistant':
                        # Check if meta-agent was invoked
                        if 'meta-agent' in str(message):
                            logger.info("Meta-agent invoked for dynamic generation")
                    
        except Exception as e:
            logger.error(f"Error during query execution: {e}")
            raise
        
        return messages
    
    async def run_interactive(self):
        """Run in interactive mode"""
        print("Dynamic Agent System - Interactive Mode")
        print("Type 'exit' to quit")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\nYour request: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Process the request
                messages = await self.process_request(user_input)
                
                # Extract and display the final result
                for msg in messages:
                    if hasattr(msg, 'type') and msg.type == 'result':
                        if hasattr(msg, 'result'):
                            print(f"\nResult:\n{msg.result}")
                        break
                
            except KeyboardInterrupt:
                print("\nInterrupted. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"\nError: {e}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dynamic Agent System")
    parser.add_argument("prompt", nargs="?", help="Direct prompt to execute")
    parser.add_argument("--working-dir", type=Path, help="Working directory")
    parser.add_argument("--max-turns", type=int, default=10, help="Maximum conversation turns")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize orchestrator
    orchestrator = DynamicAgentOrchestrator(working_dir=args.working_dir)
    
    if args.prompt:
        # Single prompt mode
        options = ClaudeCodeOptions(max_turns=args.max_turns)
        messages = await orchestrator.process_request(args.prompt, options)
        
        # Print final result
        for msg in messages:
            if hasattr(msg, 'type') and msg.type == 'result' and hasattr(msg, 'result'):
                print(msg.result)
                break
    else:
        # Interactive mode
        await orchestrator.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())