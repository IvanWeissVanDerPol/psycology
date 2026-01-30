#!/usr/bin/env python3
"""
Run multiple transcription processes in parallel - one per chat.
Each process loads its own model and saves incrementally.

Usage:
    python transcribe_all_parallel.py [--max-workers 3]
"""

import argparse
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TRANSCRIPTS_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "whatsapp transcripts"
SCRIPTS_DIR = Path(__file__).parent


def get_chats_to_process():
    """Get list of chats with their file counts."""
    chats = []
    for d in TRANSCRIPTS_DIR.iterdir():
        if d.is_dir():
            files = list(d.glob("*.opus"))
            if files:
                chats.append((d.name, len(files)))
    return sorted(chats, key=lambda x: x[1])  # Smallest first


def run_transcription(chat_name: str, model: str = "tiny") -> tuple:
    """Run transcription for a single chat in a subprocess."""
    script = SCRIPTS_DIR / "transcribe_resumable.py"
    try:
        result = subprocess.run(
            [sys.executable, str(script), chat_name, "--model", model],
            capture_output=True,
            text=True,
            timeout=7200,  # 2 hour timeout per chat
        )
        return (chat_name, True, result.stdout[-500:] if result.stdout else "")
    except subprocess.TimeoutExpired:
        return (chat_name, False, "Timeout")
    except Exception as e:
        return (chat_name, False, str(e))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
        help="Max parallel processes (default: 3, safe for memory)",
    )
    parser.add_argument("--model", default="tiny")
    args = parser.parse_args()

    chats = get_chats_to_process()

    print(f"{'=' * 60}")
    print(f"PARALLEL TRANSCRIPTION - {args.max_workers} workers")
    print(f"{'=' * 60}")
    print(f"\nChats to process ({len(chats)} total):")
    for name, count in chats:
        print(f"  {name}: {count} files")
    print()

    start_time = time.time()
    completed = 0

    with ProcessPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {
            executor.submit(run_transcription, name, args.model): name
            for name, _ in chats
        }

        for future in as_completed(futures):
            chat_name = futures[future]
            try:
                name, success, output = future.result()
                status = "✓" if success else "✗"
                print(f"\n[{status}] {name} completed")
                if output:
                    # Show last few lines
                    lines = output.strip().split("\n")
                    for line in lines[-3:]:
                        print(f"    {line}")
            except Exception as e:
                print(f"\n[✗] {chat_name} failed: {e}")

            completed += 1
            elapsed = time.time() - start_time
            print(
                f"\nProgress: {completed}/{len(chats)} chats | Elapsed: {elapsed / 60:.1f}m"
            )

    print(f"\n{'=' * 60}")
    print(f"ALL DONE in {(time.time() - start_time) / 60:.1f} minutes")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
