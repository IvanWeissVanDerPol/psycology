#!/usr/bin/env python3
"""Run transcription for all remaining files sequentially."""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "transcribe_resumable.py"

# Chats to process in order
CHATS = ["Lourdes", "Laura"]

for chat in CHATS:
    print(f"\n{'=' * 60}")
    print(f"Processing: {chat}")
    print("=" * 60)

    cmd = [
        sys.executable,
        "-u",
        str(SCRIPT),
        chat,
        "--retry-failed",
        "--model",
        "medium",
    ]

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"WARNING: {chat} exited with code {result.returncode}")

print("\n*** ALL DONE ***")
