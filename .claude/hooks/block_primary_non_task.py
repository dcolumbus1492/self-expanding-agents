#!/usr/bin/env python3
"""PreToolUse hook: ensure the primary agent only ever uses the Task tool

If the caller is the root (primary) agent and it tries any tool other than
`Task`, we block the call with exit-code 2 so Claude falls back to delegating.
We identify the primary agent by the fact that there is **no** `subagent_type`
field inside `tool_input`.  Any real sub-agent invocation includes that field.

This is intentionally minimal – we do not log to files, only stderr.
"""

import json
import sys

try:
    data = json.load(sys.stdin)
except Exception:
    # If we can't parse, allow by default (avoid accidental lock-out)
    sys.exit(0)

tool_name = data.get("tool_name", "")
from pathlib import Path
LOCK_FILE = Path(".primary_locked")
subagent_type = data.get("tool_input", {}).get("subagent_type", "")

# Enforce after first restart (lock file exists)
if LOCK_FILE.exists() and not subagent_type and tool_name != "Task": 
    print(f"⛔ Primary agent may only use Task tool (attempted {tool_name})", file=sys.stderr)
    sys.exit(2)  # block the tool call

# Otherwise allow
sys.exit(0)
