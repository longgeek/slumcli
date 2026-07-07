import json
import subprocess

from datetime import datetime
from pathlib import Path
from slumcli.security import is_command_blocked

ROOT_DIR = Path(__file__).parent.parent

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the file to read"
                    }
                },
                "required": ["path"]
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                    }
                },
                "required": ["path", "content"]
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_replace",
            "description": "Search and replace in a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_string": {
                        "type": "string",
                        "description": "The pattern to search for"
                    },
                    "new_string": {
                        "type": "string",
                        "description": "The replacement for the pattern"
                    },
                    "path": {
                        "type": "string",
                        "description": "The path to the file to search and replace in"
                    }
                },
                "required": ["old_string", "new_string", "path"]
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a command",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to run"
                    },
                },
                "required": ["command"]
            }
        },
    }
]

def get_current_time(arguments) -> str:  
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def read_file(arguments):
    data = json.loads(arguments)
    path = data.get("path", "")
    full = (ROOT_DIR / path).resolve()
    if not full.is_relative_to(ROOT_DIR.resolve()):
        raise ValueError("Invalid path")
    with open(full, "r") as file:
        return file.read()
    
def write_file(arguments):
    data = json.loads(arguments)
    path = data.get("path", "")
    content = data.get("content", "")
    full = (ROOT_DIR / path).resolve()
    if not full.is_relative_to(ROOT_DIR.resolve()):
        raise ValueError("Invalid path")
    with open(full, "w") as file:
        file.write(content)
    return "File written successfully"

def search_replace(arguments):
    data = json.loads(arguments)
    content = read_file(arguments)
    old_string = data.get("old_string", "")
    new_string = data.get("new_string", "")
    if old_string not in content:
        return "Old string not found in file"
    
    content = content.replace(old_string, new_string)
    data["content"] = content
    write_file(json.dumps(data))
    return "Search and replace completed successfully"

def run_command(arguments):
    data = json.loads(arguments)
    command = data.get("command", "")
    if is_command_blocked(command):
        return "Command is blocked"
    try:
        result = subprocess.run(command, cwd=ROOT_DIR, shell=True, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return "Command timed out"
    if result.returncode != 0:
        return f"Command failed with return code {result.returncode}: {result.stderr}"
    return f"Command executed successfully: {result.stdout}"

TOOLS_HANDLERS = {
    "read_file": read_file,
    "write_file": write_file,
    "get_current_time": get_current_time,
    "search_replace": search_replace,
    "run_command": run_command,
}

def run_tool(name, arguments):
    try:
        if name not in TOOLS_HANDLERS:
            return f"Error: unknown tool '{name}'"
        return TOOLS_HANDLERS[name](arguments)
    except json.JSONDecodeError:
        return "Error: invalid tool arguments"
    except ValueError as e:
        return f"Error: {e}"
    except FileNotFoundError:
        return "Error: file not found"
    except Exception as e:
        return f"Error: {e}"