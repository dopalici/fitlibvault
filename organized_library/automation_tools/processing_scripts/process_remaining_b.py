#!/usr/bin/env python3
"""
Process remaining B42-B48 files
"""

import os
import sys
import subprocess
from pathlib import Path

# Change to parent directory
parent_dir = Path(__file__).parent.parent
os.chdir(parent_dir)

print(f"Working directory: {os.getcwd()}")

# Check files exist
for i in range(42, 49):
    pattern = f"B{i}. *.md"
    files = list(Path('.').glob(pattern))
    if files:
        print(f"Found: {files[0]}")
    else:
        print(f"Missing: B{i}")

# Run processing (set ANTHROPIC_API_KEY in your environment first)
script = Path(__file__).resolve().parent / "process_fitness_library.py"
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("Error: set ANTHROPIC_API_KEY, e.g. export ANTHROPIC_API_KEY='sk-ant-...'", file=sys.stderr)
    sys.exit(1)

cmd = [
    "python3", str(script),
    "--section", "B",
    "--start-num", "42",
    "--end-num", "48",
    "--input-dir", ".",
    "--output-dir", "processed_notes",
    "--api-key", api_key,
]

print("Running command:", "python3", script, "(with --api-key redacted)")
result = subprocess.run(cmd)
sys.exit(result.returncode)