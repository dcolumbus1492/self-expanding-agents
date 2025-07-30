# Common Workflow Patterns for Dynamic Agents

## File Analysis Pattern
```
1. Use Read tool to examine target files
2. Use Grep tool to find specific patterns
3. Use Write/MultiEdit to make changes
4. Use Bash to validate changes
```

## Code Generation Pattern
```
1. Analyze requirements with existing files (Read/Grep)
2. Generate code using Write tool
3. Create tests using Write tool
4. Execute validation using Bash tool
```

## Data Processing Pattern
```
1. Read input data files (Read tool)
2. Process with bash scripts (Bash tool)
3. Generate output files (Write tool)
4. Validate results (Bash/Read tools)
```

## API Integration Pattern
```
1. Generate curl scripts (Write tool)
2. Execute API calls (Bash tool)
3. Process responses (Read/Write tools)
4. Handle errors and retries (Bash tool)
```

## Testing & Validation Pattern
```
1. Analyze code structure (Read/Grep tools)
2. Generate test files (Write tool)
3. Execute tests (Bash tool)
4. Report results (Write tool)
```

## Debugging & Analysis Pattern
```
1. Search for error patterns (Grep tool)
2. Analyze log files (Read tool)
3. Generate diagnostic scripts (Write/Bash tools)
4. Create fix suggestions (Write tool)
```