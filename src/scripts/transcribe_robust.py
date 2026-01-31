#!/usr/bin/env python3
"""
Robust transcription wrapper - retries all failed files across all chats.
Includes watchdog to detect and recover from hangs.

Usage:
    python transcribe_robust.py --model medium
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TRANSCRIPTS_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "voice_note_transcripts"
SOURCE_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "whatsapp transcripts"


def get_status():
    """Get current transcription status for all chats."""
    status = {}

    for source_dir in SOURCE_DIR.iterdir():
        if not source_dir.is_dir():
            continue

        chat_name = source_dir.name
        opus_files = list(source_dir.glob("*.opus"))
        total = len(opus_files)

        if total == 0:
            continue

        # Check transcripts
        json_path = TRANSCRIPTS_DIR / chat_name / "transcripts.json"
        success = 0
        failed = 0

        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            success = sum(1 for t in data if t.get("success"))
            failed = sum(1 for t in data if not t.get("success"))

        remaining = total - success
        status[chat_name] = {
            "total": total,
            "success": success,
            "failed": failed,
            "remaining": remaining,
        }

    return status


def print_status(status):
    """Print status table."""
    print("\n" + "=" * 60)
    print(f"{'Chat':<25} {'Done':<8} {'Failed':<8} {'Total':<8} {'%':<6}")
    print("=" * 60)

    total_done = 0
    total_files = 0

    for chat, s in sorted(status.items(), key=lambda x: x[1]["remaining"]):
        pct = 100 * s["success"] / s["total"] if s["total"] > 0 else 0
        marker = "[DONE]" if s["remaining"] == 0 else ""
        print(
            f"{chat:<25} {s['success']:<8} {s['failed']:<8} {s['total']:<8} {pct:>5.1f}% {marker}"
        )
        total_done += s["success"]
        total_files += s["total"]

    print("=" * 60)
    overall_pct = 100 * total_done / total_files if total_files > 0 else 0
    print(
        f"{'TOTAL':<25} {total_done:<8} {'':<8} {total_files:<8} {overall_pct:>5.1f}%"
    )
    print("=" * 60 + "\n")


def run_transcription(chat_name: str, model: str, retry_failed: bool = True):
    """Run transcription for a single chat."""
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "transcribe_resumable.py"),
        chat_name,
        "--model",
        model,
    ]
    if retry_failed:
        cmd.append("--retry-failed")

    print(f"\nRunning: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        last_output_time = time.time()

        while True:
            if process.stdout is None:
                break
            line = process.stdout.readline()
            if line:
                print(line, end="", flush=True)
                last_output_time = time.time()

            # Check if process finished
            if process.poll() is not None:
                break

            # Watchdog: if no output for 5 minutes, something is wrong
            if time.time() - last_output_time > 300:
                print("\n⚠️ WATCHDOG: No output for 5 minutes, killing process...")
                process.kill()
                return False

            time.sleep(0.1)

        return process.returncode == 0

    except Exception as e:
        print(f"Error running transcription: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Robust transcription for all chats")
    parser.add_argument("--model", default="medium", help="Whisper model")
    parser.add_argument(
        "--max-retries", type=int, default=3, help="Max retries per chat"
    )
    args = parser.parse_args()

    print(f"Starting robust transcription with model: {args.model}")

    while True:
        status = get_status()
        print_status(status)

        # Find chats with remaining work
        incomplete = [(chat, s) for chat, s in status.items() if s["remaining"] > 0]

        if not incomplete:
            print("*** All transcriptions complete! ***")
            break

        # Sort by remaining (smallest first for quick wins)
        incomplete.sort(key=lambda x: x[1]["remaining"])

        chat_name, s = incomplete[0]
        print(f"\n>>> Processing: {chat_name} ({s['remaining']} remaining)")

        success = run_transcription(chat_name, args.model, retry_failed=True)

        if not success:
            print(f"WARNING: {chat_name} had issues, will retry later...")
            time.sleep(10)

        # Brief pause between chats
        time.sleep(2)

    # Final status
    print("\n" + "=" * 60)
    print("FINAL STATUS")
    print_status(get_status())


if __name__ == "__main__":
    main()
