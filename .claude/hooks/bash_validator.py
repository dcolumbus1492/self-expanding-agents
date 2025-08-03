#!/usr/bin/env python3
"""
Bash Command Security Validator for Claude Code Hooks

This script validates bash commands for potential security risks and dangerous operations.
It's designed to be used as a PreToolUse hook to prevent execution of risky commands.
"""

import json
import sys
import re
from typing import List, Dict, Any

# Dangerous command patterns that should be blocked
DANGEROUS_PATTERNS = [
    # Data destruction
    r'\brm\s+(-[rf]*\s+)?(/|\$HOME|\~)',  # rm -rf /, rm -rf ~, etc.
    r'\bdd\s+.*of\s*=\s*/dev/',           # dd writing to /dev/
    r':\(\)\{.*\}.*:',                    # Fork bomb pattern
    r'\bchmod\s+777',                     # Overly permissive permissions
    
    # Network operations that could be risky
    r'\bcurl\s+.*\|\s*(bash|sh)',         # curl | bash (downloading and executing)
    r'\bwget\s+.*\|\s*(bash|sh)',         # wget | bash
    r'\bnc\s+.*-e',                       # netcat with execute
    
    # System modification
    r'\bchroot\s+',                       # chroot operations
    r'\bmkfs\.',                          # filesystem creation
    r'\bfdisk\s+',                        # disk partitioning
    
    # Privilege escalation
    r'\bsudo\s+.*-u\s+root',             # sudo as root (context dependent)
    r'\bsu\s+-\s+',                      # switch user
    
    # Process manipulation
    r'\bkill\s+-9\s+1',                  # killing init
    r'\bkillall\s+-9',                   # killing all processes
    
    # File system manipulation
    r'\bmount\s+.*-o.*exec',             # mounting with exec
    r'\bumount\s+/\s*$',                 # unmounting root
]

# Commands that require careful review
SUSPICIOUS_PATTERNS = [
    r'\bsudo\s+',                        # Any sudo usage
    r'\beval\s+',                        # eval command
    r'\bexec\s+',                        # exec command
    r'`[^`]*`',                          # Command substitution with backticks
    r'\$\([^)]*\)',                      # Command substitution with $()
    r'>\s*/dev/null\s+2>&1\s*&',        # Background execution hiding output
    r'\bnohup\s+',                       # Background process that persists
    r'\bcrontab\s+-e',                   # Crontab editing
    r'\bsystemctl\s+(enable|disable|start|stop)', # System service control
]

def check_dangerous_patterns(command: str) -> List[str]:
    """Check if command matches any dangerous patterns."""
    violations = []
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            violations.append(f"Dangerous pattern detected: {pattern}")
    return violations

def check_suspicious_patterns(command: str) -> List[str]:
    """Check if command matches any suspicious patterns."""
    warnings = []
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            warnings.append(f"Suspicious pattern detected: {pattern}")
    return warnings

def validate_command(tool_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a bash command for security risks.
    
    Returns:
        Dict with 'allowed', 'violations', 'warnings', and 'message' keys
    """
    tool_input = tool_data.get('tool_input', {})
    command = tool_input.get('command', '')
    description = tool_input.get('description', 'No description')
    
    if not command:
        return {
            'allowed': True,
            'violations': [],
            'warnings': [],
            'message': 'No command to validate'
        }
    
    violations = check_dangerous_patterns(command)
    warnings = check_suspicious_patterns(command)
    
    # Block if any dangerous patterns found
    allowed = len(violations) == 0
    
    message_parts = []
    if violations:
        message_parts.append(f"BLOCKED: Command contains dangerous patterns:")
        for violation in violations:
            message_parts.append(f"  - {violation}")
        message_parts.append(f"Command: {command}")
        message_parts.append("This command has been blocked for security reasons.")
    
    if warnings:
        message_parts.append(f"WARNING: Command contains suspicious patterns:")
        for warning in warnings:
            message_parts.append(f"  - {warning}")
        message_parts.append(f"Command: {command}")
        message_parts.append("Please review this command carefully.")
    
    return {
        'allowed': allowed,
        'violations': violations,
        'warnings': warnings,
        'message': '\n'.join(message_parts) if message_parts else 'Command appears safe'
    }

def main():
    """Main function for use as a Claude Code hook."""
    try:
        # Read JSON input from stdin
        tool_data = json.load(sys.stdin)
        
        # Validate the command
        result = validate_command(tool_data)
        
        # Log the validation result
        with open('/tmp/claude_bash_validator.log', 'a') as log_file:
            log_entry = {
                'command': tool_data.get('tool_input', {}).get('command', ''),
                'allowed': result['allowed'],
                'violations': result['violations'],
                'warnings': result['warnings']
            }
            log_file.write(json.dumps(log_entry) + '\n')
        
        # If violations found, print message to stderr and exit with code 2
        if result['violations']:
            print(result['message'], file=sys.stderr)
            sys.exit(2)  # Exit code 2 blocks the tool execution
        
        # If warnings found, print to stderr but allow execution
        if result['warnings']:
            print(result['message'], file=sys.stderr)
        
        sys.exit(0)  # Allow execution
        
    except Exception as e:
        print(f"Error in bash validator: {e}", file=sys.stderr)
        sys.exit(0)  # Allow execution on validator errors to avoid blocking legitimate commands

if __name__ == '__main__':
    main()