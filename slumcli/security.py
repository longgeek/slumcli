from pathlib import Path
from datetime import datetime

LOG = Path(__file__).parent.parent / "audit.log"
DANGEROUS_TOOLS = ["write_file", "search_replace", "run_command"]
DANGEROUS_COMMANDS = ["rm -fr", "mkfs", "dd if", "curl"]

def confirm_tool(name, arguments):
    if name in DANGEROUS_TOOLS:
        print(f"Are you sure you want to use the {name} tool? (y/n): ")
        return input().lower() == "y"
    return True

def is_command_blocked(command):
    print(f"Checking command: {command}")
    for item in DANGEROUS_COMMANDS:
        if item in command:
            print(f"Command is blocked: {command}")
            return True
    return False

def audit_log(name, arguments, outcome):
    with open(LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()} - {name} - {arguments} - {outcome}\n")