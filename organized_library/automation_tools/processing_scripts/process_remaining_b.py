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

# Run processing
cmd = [
    "python3", "automation_scripts/process_fitness_library.py",
    "--section", "B",
    "--start-num", "42",
    "--end-num", "48", 
    "--input-dir", ".",
    "--output-dir", "processed_notes",
    "--api-key", "sk-ant-api03-MyMy97vMN61gh8drHm4MU_3bxnVyQbT27EiUzEovf2a6XkOmCSbLLW4SBVetWxyEV32IuHuNfEWxBMrda6_7Yw-9eKLgAAA"
]

print("Running command:", ' '.join(cmd))
result = subprocess.run(cmd)
sys.exit(result.returncode)