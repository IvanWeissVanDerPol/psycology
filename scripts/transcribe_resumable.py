#!/usr/bin/env python3
"""
Resumable transcription - saves progress after EVERY file.
Can be stopped and resumed at any time.

Usage:
    python transcribe_resumable.py Laura
    python transcribe_resumable.py --all
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

# FFmpeg
os.environ["PATH"] = (
    r"C:\Users\Alejandro\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin"
    + os.pathsep
    + os.environ.get("PATH", "")
)

BASE_DIR = Path(__file__).parent.parent
TRANSCRIPTS_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "whatsapp transcripts"
OUTPUT_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "voice_note_transcripts"


def load_progress(chat_name: str) -> dict:
    """Load existing progress for a chat."""
    json_path = OUTPUT_DIR / chat_name / "transcripts.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {item["file"]: item for item in data}
        except Exception:
            pass
    return {}


def save_progress(chat_name: str, results: dict):
    """Save current progress to disk."""
    out_dir = OUTPUT_DIR / chat_name
    out_dir.mkdir(parents=True, exist_ok=True)

    items = list(results.values())

    # JSON
    with open(out_dir / "transcripts.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    # Markdown
    by_date = {}
    for r in items:
        d = r.get("date") or "unknown"
        by_date.setdefault(d, []).append(r)

    success = sum(1 for r in items if r.get("success"))
    with open(out_dir / "transcripts.md", "w", encoding="utf-8") as f:
        f.write(f"# Voice Notes: {chat_name}\n\n")
        f.write(
            f"> {success}/{len(items)} successful | {datetime.now():%Y-%m-%d %H:%M}\n\n---\n\n"
        )
        for date in sorted(by_date):
            f.write(f"## {date}\n\n")
            for r in sorted(by_date[date], key=lambda x: x["file"]):
                f.write(f"### {r['file']}\n\n")
                if r.get("text"):
                    f.write(f"{r['text']}\n\n")
                elif r.get("error"):
                    f.write(f"*Error: {r['error']}*\n\n")
            f.write("---\n\n")


def parse_date(filename: str) -> str | None:
    """Extract date from filename like PTT-20240902-WA0017.opus"""
    try:
        parts = filename.split("-")
        if len(parts) >= 2 and len(parts[1]) == 8:
            return f"{parts[1][:4]}-{parts[1][4:6]}-{parts[1][6:8]}"
    except Exception:
        pass
    return None


def transcribe_chat(
    chat_name: str,
    model_name: str = "tiny",
    language: str = "es",
    retry_failed: bool = False,
):
    """Transcribe a single chat with resume support.

    Args:
        retry_failed: If True, also retry files that previously failed
    """
    import gc
    import torch

    # Find chat folder
    chat_dir = None
    for d in TRANSCRIPTS_DIR.iterdir():
        if chat_name.lower() in d.name.lower():
            chat_dir = d
            break

    if not chat_dir:
        print(f"Chat '{chat_name}' not found")
        return

    files = sorted(chat_dir.glob("*.opus"))
    if not files:
        print(f"No .opus files in {chat_dir.name}")
        return

    # Load existing progress
    results = load_progress(chat_dir.name)

    # Determine which files need processing
    if retry_failed:
        # Skip only successful files
        done_files = {f for f, r in results.items() if r.get("success")}
        failed_count = sum(1 for r in results.values() if not r.get("success"))
    else:
        # Skip both successful and failed files
        done_files = set(results.keys())
        failed_count = 0

    remaining = [f for f in files if f.name not in done_files]

    if retry_failed and failed_count > 0:
        print(f"  (Retrying {failed_count} previously failed files)")

    print(f"\n{'=' * 60}")
    print(f"Chat: {chat_dir.name}")
    print(f"Total files: {len(files)}")
    print(f"Already done: {len(done_files)}")
    print(f"Remaining: {len(remaining)}")
    print(f"{'=' * 60}\n")

    if not remaining:
        print("All files already transcribed!")
        return

    # Load model
    import whisper

    print(f"Loading Whisper '{model_name}'...")
    model = whisper.load_model(model_name)
    print("Model ready.\n")

    start = datetime.now()

    for i, f in enumerate(remaining):
        try:
            # Use fp16=True for GPU acceleration
            r = model.transcribe(str(f), language=language, fp16=True, verbose=False)
            text = r["text"]
            if isinstance(text, str):
                text = text.strip()
            else:
                text = str(text).strip() if text else ""
            results[f.name] = {
                "file": f.name,
                "date": parse_date(f.name),
                "text": text,
                "duration": r.get("duration"),
                "success": True,
            }
        except Exception as e:
            results[f.name] = {
                "file": f.name,
                "date": parse_date(f.name),
                "error": str(e),
                "success": False,
            }

        # Save after EVERY file
        save_progress(chat_dir.name, results)

        # Aggressive memory cleanup every 50 files (helps with Windows memory issues)
        if (i + 1) % 50 == 0:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        # Progress update
        total_done = len(done_files) + i + 1
        elapsed = (datetime.now() - start).total_seconds()
        rate = (i + 1) / elapsed if elapsed > 0 else 0
        eta = (len(remaining) - i - 1) / rate / 60 if rate > 0 else 0

        if (i + 1) % 10 == 0 or i == len(remaining) - 1:
            print(
                f"  {total_done}/{len(files)} ({100 * total_done / len(files):.1f}%) | "
                f"{rate:.2f}/sec | ETA: {eta:.1f}m | Saved: {chat_dir.name}"
            )

    elapsed = (datetime.now() - start).total_seconds()
    success = sum(1 for r in results.values() if r.get("success"))
    print(f"\nDone: {success}/{len(files)} successful in {elapsed / 60:.1f}m")


def main():
    parser = argparse.ArgumentParser(
        description="Resumable transcription - saves progress after EVERY file."
    )
    parser.add_argument("chat", nargs="?", help="Chat name (e.g., Laura)")
    parser.add_argument("--all", action="store_true", help="Process all chats")
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry previously failed transcriptions (memory errors, etc.)",
    )
    parser.add_argument(
        "--model",
        default="tiny",
        help="Whisper model: tiny, base, small, medium, large (default: tiny)",
    )
    parser.add_argument("--language", default="es", help="Language code (default: es)")
    args = parser.parse_args()

    if args.all:
        # Process all chats, smallest first
        chats = []
        for d in TRANSCRIPTS_DIR.iterdir():
            if d.is_dir():
                files = list(d.glob("*.opus"))
                if files:
                    chats.append((d.name, len(files)))

        chats.sort(key=lambda x: x[1])  # Smallest first

        mode = "RETRY FAILED" if args.retry_failed else "NEW ONLY"
        print(f"\nMode: {mode}")
        print(f"Will process {len(chats)} chats:")
        for name, count in chats:
            print(f"  {name}: {count} files")
        print()

        for name, _ in chats:
            transcribe_chat(name, args.model, args.language, args.retry_failed)

    elif args.chat:
        transcribe_chat(args.chat, args.model, args.language, args.retry_failed)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
