#!/usr/bin/env python3
"""
Update all hook files to use timestamped session directory names
"""

import re
from pathlib import Path


def update_hook_file(file_path):
    """Update a hook file to use timestamped session directory names"""
    print(f"Updating {file_path}...")

    with open(file_path, 'r') as f:
        content = f.read()

    # Check if file needs updating
    if 'f"session_{session_id}"' not in content:
        print(f"  ⚠️  No session directory references found in {file_path}")
        return False

    # Add datetime import if not present
    if 'from datetime import datetime' not in content and 'import datetime' not in content:
        # Find the import section and add datetime
        imports_pattern = r'(import [^\n]*\n)+'
        if re.search(imports_pattern, content):
            content = re.sub(
                r'(import [^\n]*\n)+',
                lambda m: m.group(0) + 'from datetime import datetime\n',
                content,
                count=1
            )
        else:
            # Add at the top after shebang/docstring
            lines = content.split('\n')
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith('"""') and '"""' in line[3:]:
                    insert_pos = i + 1
                    break
                elif line.startswith('"""'):
                    # Multi-line docstring
                    for j in range(i + 1, len(lines)):
                        if '"""' in lines[j]:
                            insert_pos = j + 1
                            break
                    break
                elif line.startswith('#!'):
                    insert_pos = i + 1

            lines.insert(insert_pos, 'from datetime import datetime')
            content = '\n'.join(lines)

    # Define the session directory creation function
    session_dir_func = '''
def get_session_dir_name(session_id):
    """Get timestamped session directory name for consistent naming"""
    # Try to extract timestamp from existing session dirs to maintain consistency
    logs_dir = Path("logs")
    if logs_dir.exists():
        existing_dirs = [d.name for d in logs_dir.iterdir() if d.is_dir() and session_id in d.name]
        if existing_dirs:
            # Use existing timestamped name
            return existing_dirs[0]

    # Create new timestamped name
    timestamp_prefix = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"session_{timestamp_prefix}_{session_id}"
'''

    # Add the helper function if not present
    if 'def get_session_dir_name(' not in content:
        # Find a good place to insert the function (after imports, before other functions)
        func_pattern = r'\n\ndef [^_]'
        match = re.search(func_pattern, content)
        if match:
            insert_pos = match.start() + 1
            content = content[:insert_pos] + session_dir_func + content[insert_pos:]
        else:
            # Insert before main() if it exists
            main_pattern = r'\ndef main\(\):'
            match = re.search(main_pattern, content)
            if match:
                insert_pos = match.start() + 1
                content = content[:insert_pos] + session_dir_func + content[insert_pos:]

    # Replace session directory references
    old_pattern = r'session_dir = logs_dir / f"session_{session_id}"'
    new_pattern = 'session_dir = logs_dir / get_session_dir_name(session_id)'

    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print(f"  ✅ Updated session directory creation")

    # Also handle find_session_directory function pattern
    find_pattern = r'session_dir = logs_dir / f"session_{session_id}"'
    if find_pattern in content:
        content = content.replace(find_pattern, 'session_dir = logs_dir / get_session_dir_name(session_id)')
        print(f"  ✅ Updated find_session_directory function")

    # Write back the updated content
    with open(file_path, 'w') as f:
        f.write(content)

    return True


def main():
    """Update all hook files with timestamped session naming"""
    print("🔄 UPDATING SESSION DIRECTORY NAMING")
    print("=" * 50)

    # Find all hook files that need updating
    hook_files = [
        Path(".claude/hooks/user_prompt_submit.py"),
        Path(".claude/hooks/subagent_stop.py"),
        Path(".claude/hooks/pre_tool_use.py"),
        Path(".claude/hooks/post_tool_use.py"),
        Path(".claude/hooks/stop.py"),
        # session_start.py already updated manually
    ]

    updated_count = 0
    for hook_file in hook_files:
        if hook_file.exists():
            if update_hook_file(hook_file):
                updated_count += 1
        else:
            print(f"⚠️  File not found: {hook_file}")

    print(f"\n✅ Updated {updated_count} hook files")
    print("📋 New session directory format: session_YYYYMMDD_HHMMSS_<session_id>")
    print("📋 This enables easy chronological sorting of session logs")


if __name__ == "__main__":
    main()
