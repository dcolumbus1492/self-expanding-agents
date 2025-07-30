"""
High-level data analysis tool module

This demonstrates a Python-based MCP tool with advanced functionality.
"""

import json
import statistics
from typing import Any, Dict, List, Union
from pathlib import Path
import csv

# Tool definition for MCP
TOOL_DEFINITION = {
    "name": "data_analyzer",
    "description": "Analyzes data files (JSON, CSV) and provides statistical insights",
    "inputSchema": {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "Path to the data file"
            },
            "operation": {
                "type": "string",
                "enum": ["summary", "statistics", "preview", "schema"],
                "description": "Type of analysis to perform"
            },
            "options": {
                "type": "object",
                "description": "Additional options for the operation",
                "properties": {
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific columns to analyze (for CSV)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Limit for preview operation"
                    }
                }
            }
        },
        "required": ["filepath", "operation"]
    }
}


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the data analysis tool"""
    filepath = Path(arguments.get('filepath', ''))
    operation = arguments.get('operation')
    options = arguments.get('options', {})
    
    if not filepath.exists():
        return {"error": f"File not found: {filepath}"}
    
    try:
        # Detect file type and load data
        if filepath.suffix.lower() == '.json':
            data = load_json_file(filepath)
        elif filepath.suffix.lower() == '.csv':
            data = load_csv_file(filepath)
        else:
            return {"error": f"Unsupported file type: {filepath.suffix}"}
        
        # Perform the requested operation
        if operation == 'summary':
            return generate_summary(data, filepath)
        elif operation == 'statistics':
            return calculate_statistics(data, options.get('columns'))
        elif operation == 'preview':
            return preview_data(data, options.get('limit', 10))
        elif operation == 'schema':
            return analyze_schema(data)
        else:
            return {"error": f"Unknown operation: {operation}"}
            
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}


def load_json_file(filepath: Path) -> Any:
    """Load and parse JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_csv_file(filepath: Path) -> List[Dict[str, str]]:
    """Load CSV file as list of dictionaries"""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def generate_summary(data: Any, filepath: Path) -> Dict[str, Any]:
    """Generate a summary of the data"""
    summary = {
        "file": str(filepath),
        "type": type(data).__name__,
    }
    
    if isinstance(data, list):
        summary["count"] = len(data)
        if data and isinstance(data[0], dict):
            summary["fields"] = list(data[0].keys())
            summary["sample"] = data[0]
    elif isinstance(data, dict):
        summary["keys"] = list(data.keys())
        summary["size"] = len(data)
    
    return {"summary": summary}


def calculate_statistics(data: List[Dict[str, Any]], columns: List[str] = None) -> Dict[str, Any]:
    """Calculate statistics for numerical columns"""
    if not isinstance(data, list) or not data:
        return {"error": "Data must be a non-empty list"}
    
    stats = {}
    
    # Determine columns to analyze
    if columns:
        cols_to_analyze = columns
    else:
        # Auto-detect numeric columns
        cols_to_analyze = []
        if isinstance(data[0], dict):
            for key in data[0].keys():
                try:
                    float(data[0][key])
                    cols_to_analyze.append(key)
                except (ValueError, TypeError):
                    pass
    
    # Calculate statistics for each column
    for col in cols_to_analyze:
        values = []
        for row in data:
            try:
                if isinstance(row, dict) and col in row:
                    values.append(float(row[col]))
            except (ValueError, TypeError):
                continue
        
        if values:
            stats[col] = {
                "count": len(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0
            }
    
    return {"statistics": stats}


def preview_data(data: Any, limit: int) -> Dict[str, Any]:
    """Preview the first N items of data"""
    if isinstance(data, list):
        preview = data[:limit]
    elif isinstance(data, dict):
        preview = dict(list(data.items())[:limit])
    else:
        preview = str(data)[:500]
    
    return {
        "preview": preview,
        "total_count": len(data) if hasattr(data, '__len__') else None,
        "showing": min(limit, len(data)) if hasattr(data, '__len__') else None
    }


def analyze_schema(data: Any) -> Dict[str, Any]:
    """Analyze the structure/schema of the data"""
    schema = {"type": type(data).__name__}
    
    if isinstance(data, list) and data:
        schema["item_type"] = type(data[0]).__name__
        if isinstance(data[0], dict):
            schema["fields"] = {}
            for key in data[0].keys():
                # Sample multiple items to determine type
                types = set()
                for item in data[:min(10, len(data))]:
                    if key in item:
                        types.add(type(item[key]).__name__)
                schema["fields"][key] = list(types)
    
    elif isinstance(data, dict):
        schema["keys"] = {}
        for key, value in data.items():
            schema["keys"][key] = type(value).__name__
    
    return {"schema": schema}