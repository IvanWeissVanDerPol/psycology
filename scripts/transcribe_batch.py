#!/usr/bin/env python3
"""
Batch transcription - processes one chat at a time with threading for I/O.
More memory efficient than full multiprocessing.
"""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Lock

# Add ffmpeg to PATH
FFMPEG_PATHS = [
    r"C:\Users\Alejandro\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin",
]
for p in FFMPEG_PATHS:
    if os.path.exists(p):
        os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")
        break

BASE_DIR = Path(__file__).parent.parent
TRANSCRIPTS_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "whatsapp transcripts"
OUTPUT_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "voice_note_transcripts"

# Single model instance with lock
_model = None
_lock = Lock()


def get_model(name: str):
    global _model
    with _lock:
        if _model is None:
            import whisper

            print(f"Loading Whisper model '{name}'...")
            _model = whisper.load_model(name)
            print("Model loaded.")
        return _model


def transcribe_file(file_path: Path, model_name: str, language: str) -> dict:
    """Transcribe single file using shared model."""
    try:
        model = get_model(model_name)
        result = model.transcribe(
            str(file_path), language=language, fp16=False, verbose=False
        )

        # Parse date from filename
        date = None
        try:
            parts = file_path.name.split("-")
            if len(parts) >= 2 and len(parts[1]) == 8:
                date = f"{parts[1][:4]}-{parts[1][4:6]}-{parts[1][6:8]}"
        except Exception:
            pass

        return {
            "file": file_path.name,
            "date": date,
            "text": result["text"].strip(),
            "duration": result.get("duration"),
            "success": True,
        }
    except Exception as e:
        return {
            "file": file_path.name,
            "date": None,
            "error": str(e),
            "text": None,
            "success": False,
        }


def save_results(chat_name: str, results: list):
    """Save transcripts to JSON and markdown."""
    out_dir = OUTPUT_DIR / chat_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # JSON
    with open(out_dir / "transcripts.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Markdown grouped by date
    by_date = {}
    for r in results:
        d = r.get("date") or "unknown"
        by_date.setdefault(d, []).append(r)

    with open(out_dir / "transcripts.md", "w", encoding="utf-8") as f:
        f.write(f"# Voice Note Transcripts: {chat_name}\n\n")
        f.write(f"> Generated: {datetime.now():%Y-%m-%d %H:%M}\n")
        f.write(f"> Total: {len(results)} files\n\n---\n\n")

        for date in sorted(by_date):
            f.write(f"## {date}\n\n")
            for r in sorted(by_date[date], key=lambda x: x["file"]):
                f.write(f"### {r['file']}\n\n")
                if r.get("error"):
                    f.write(f"**ERROR:** {r['error']}\n\n")
                elif r.get("text"):
                    f.write(f"{r['text']}\n\n")
                else:
                    f.write("*[Empty]*\n\n")
            f.write("---\n\n")


def process_chat(
    chat_name: str, files: list, model_name: str, language: str, threads: int
):
    """Process all files for one chat."""
    print(f"\n{'=' * 60}")
    print(f"Processing: {chat_name} ({len(files)} files)")
    print(f"{'=' * 60}")

    results = []
    completed = 0
    start = datetime.now()

    # Use threads for I/O parallelism (model is thread-safe for inference)
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {
            executor.submit(transcribe_file, f, model_name, language): f for f in files
        }

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1

            if completed % 100 == 0 or completed == len(files):
                elapsed = (datetime.now() - start).total_seconds()
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (len(files) - completed) / rate / 60 if rate > 0 else 0
                errors = sum(1 for r in results if not r.get("success"))
                print(
                    f"  {completed}/{len(files)} ({100 * completed / len(files):.1f}%) | "
                    f"{rate:.1f}/sec | ETA: {eta:.1f}m | Errors: {errors}"
                )

    save_results(chat_name, results)
    elapsed = (datetime.now() - start).total_seconds()
    errors = sum(1 for r in results if not r.get("success"))
    print(f"  Done: {len(results)} files in {elapsed:.1f}s ({errors} errors)")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", default="tiny", choices=["tiny", "base", "small", "medium"]
    )
    parser.add_argument("--language", default="es")
    parser.add_argument(
        "--threads", type=int, default=4, help="Threads per chat (for I/O)"
    )
    parser.add_argument("--chat", help="Process only specific chat")
    parser.add_argument(
        "--skip-done", action="store_true", help="Skip chats with existing transcripts"
    )
    args = parser.parse_args()

    # Find all chats
    chats = {}
    for d in TRANSCRIPTS_DIR.iterdir():
        if d.is_dir():
            files = sorted(d.glob("*.opus"))
            if files:
                if args.chat and args.chat.lower() not in d.name.lower():
                    continue
                chats[d.name] = files

    if not chats:
        print("No voice notes found!")
        return

    # Summary
    total = sum(len(f) for f in chats.values())
    print(f"Found {total} voice notes in {len(chats)} chats")
    for name, files in sorted(chats.items(), key=lambda x: -len(x[1])):
        print(f"  {name}: {len(files)}")

    # Process each chat
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for chat_name, files in sorted(
        chats.items(), key=lambda x: len(x[1])
    ):  # Smallest first
        # Skip if already done
        if args.skip_done:
            existing = OUTPUT_DIR / chat_name / "transcripts.json"
            if existing.exists():
                try:
                    with open(existing) as f:
                        data = json.load(f)
                    success = sum(1 for d in data if d.get("success"))
                    if success >= len(files) * 0.9:  # 90% success = done
                        print(
                            f"\n[{chat_name}] Already done ({success}/{len(files)}), skipping"
                        )
                        continue
                except Exception:
                    pass

        process_chat(chat_name, files, args.model, args.language, args.threads)

    print(f"\n{'=' * 60}")
    print("COMPLETE")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
