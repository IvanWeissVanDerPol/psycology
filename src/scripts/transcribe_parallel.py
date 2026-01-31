#!/usr/bin/env python3
"""
Parallel Voice Note Transcription using multiple workers.

Uses multiprocessing to transcribe multiple files simultaneously,
dramatically reducing total processing time.

Usage:
    python transcribe_parallel.py [--workers 4] [--model base]
"""

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add ffmpeg to PATH
FFMPEG_PATHS = [
    r"C:\Users\Alejandro\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin",
    r"C:\ffmpeg\bin",
    r"C:\Program Files\ffmpeg\bin",
]
for ffmpeg_path in FFMPEG_PATHS:
    if os.path.exists(ffmpeg_path):
        os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ.get("PATH", "")
        break

# Configuration
BASE_DIR = Path(__file__).parent.parent
TRANSCRIPTS_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "whatsapp transcripts"
OUTPUT_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "voice_note_transcripts"

# Global model cache per process
_model = None
_model_name = None


def get_model(model_name: str):
    """Get or load whisper model (cached per process)."""
    global _model, _model_name
    if _model is None or _model_name != model_name:
        import whisper

        _model = whisper.load_model(model_name)
        _model_name = model_name
    return _model


def parse_date_from_filename(filename: str) -> Optional[str]:
    """Extract date from filename."""
    try:
        parts = filename.split("-")
        if len(parts) >= 2:
            date_str = parts[1]
            if len(date_str) == 8:
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    except Exception:
        pass
    return None


def transcribe_single_file(args: tuple) -> dict:
    """Transcribe a single file. Used by process pool."""
    file_path, model_name, language = args
    file_path = Path(file_path)

    try:
        model = get_model(model_name)
        result = model.transcribe(
            str(file_path),
            language=language,
            fp16=False,
            verbose=False,
        )
        return {
            "file": file_path.name,
            "date": parse_date_from_filename(file_path.name),
            "text": result["text"].strip(),
            "language": result.get("language", language),
            "duration": result.get("duration"),
            "success": True,
        }
    except Exception as e:
        return {
            "file": file_path.name,
            "date": parse_date_from_filename(file_path.name),
            "error": str(e),
            "text": None,
            "success": False,
        }


def get_all_voice_notes() -> dict[str, list[Path]]:
    """Get all voice notes organized by chat."""
    voice_notes = {}
    for chat_dir in TRANSCRIPTS_DIR.iterdir():
        if not chat_dir.is_dir():
            continue
        opus_files = sorted(chat_dir.glob("*.opus"))
        if opus_files:
            voice_notes[chat_dir.name] = opus_files
    return voice_notes


def get_already_transcribed(chat_name: str) -> set[str]:
    """Get set of already transcribed files for a chat."""
    json_path = OUTPUT_DIR / chat_name / "transcripts.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {t["file"] for t in data if t.get("text") and not t.get("error")}
        except Exception:
            pass
    return set()


def save_transcripts(chat_name: str, transcripts: list[dict]):
    """Save transcripts to JSON and markdown."""
    chat_output_dir = OUTPUT_DIR / chat_name
    chat_output_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_path = chat_output_dir / "transcripts.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(transcripts, f, ensure_ascii=False, indent=2)

    # Save markdown
    md_path = chat_output_dir / "transcripts.md"
    by_date = {}
    for t in transcripts:
        date = t.get("date") or "unknown"
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(t)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Voice Note Transcripts: {chat_name}\n\n")
        f.write(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"> Total files: {len(transcripts)}\n\n")
        f.write("---\n\n")

        for date in sorted(by_date.keys()):
            f.write(f"## {date}\n\n")
            for t in sorted(by_date[date], key=lambda x: x["file"]):
                f.write(f"### {t['file']}\n\n")
                if t.get("error"):
                    f.write(f"**ERROR:** {t['error']}\n\n")
                elif t.get("text"):
                    f.write(f"{t['text']}\n\n")
                else:
                    f.write("*[Empty or inaudible]*\n\n")
            f.write("---\n\n")


def main():
    parser = argparse.ArgumentParser(description="Parallel voice note transcription")
    parser.add_argument(
        "--workers", type=int, default=4, help="Number of parallel workers (default: 4)"
    )
    parser.add_argument(
        "--model", default="base", choices=["tiny", "base", "small", "medium", "large"]
    )
    parser.add_argument("--language", default="es", help="Language code (default: es)")
    parser.add_argument(
        "--resume", action="store_true", help="Skip already transcribed files"
    )
    parser.add_argument("--chat", default=None, help="Process only specific chat")
    args = parser.parse_args()

    print(f"=" * 60)
    print(f"PARALLEL VOICE NOTE TRANSCRIPTION")
    print(f"Workers: {args.workers} | Model: {args.model} | Language: {args.language}")
    print(f"=" * 60)

    # Get all voice notes
    all_notes = get_all_voice_notes()

    if args.chat:
        all_notes = {
            k: v for k, v in all_notes.items() if args.chat.lower() in k.lower()
        }

    if not all_notes:
        print("No voice notes found!")
        return

    # Summary
    total = sum(len(files) for files in all_notes.values())
    print(f"\nFound {total} voice notes across {len(all_notes)} chats:\n")
    for chat, files in sorted(all_notes.items(), key=lambda x: -len(x[1])):
        print(f"  {chat}: {len(files)} files")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Collect all files to process
    all_files = []
    for chat_name, files in all_notes.items():
        if args.resume:
            already_done = get_already_transcribed(chat_name)
            files = [f for f in files if f.name not in already_done]
            if not files:
                print(f"\n[{chat_name}] All files already transcribed, skipping.")
                continue

        for f in files:
            all_files.append((chat_name, f))

    if not all_files:
        print("\nAll files already transcribed!")
        return

    print(f"\nProcessing {len(all_files)} files with {args.workers} workers...\n")

    # Prepare work items: (file_path, model_name, language)
    work_items = [(str(f), args.model, args.language) for _, f in all_files]
    file_to_chat = {str(f): chat for chat, f in all_files}

    # Process with thread pool
    results_by_chat = {}
    completed = 0
    errors = 0

    start_time = datetime.now()

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(transcribe_single_file, item): item[0]
            for item in work_items
        }

        # Process as they complete
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            chat_name = file_to_chat[file_path]

            try:
                result = future.result()

                if chat_name not in results_by_chat:
                    results_by_chat[chat_name] = []
                results_by_chat[chat_name].append(result)

                completed += 1
                if not result.get("success"):
                    errors += 1

                # Progress update every 50 files
                if completed % 50 == 0 or completed == len(all_files):
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = completed / elapsed if elapsed > 0 else 0
                    eta = (len(all_files) - completed) / rate if rate > 0 else 0
                    print(
                        f"  Progress: {completed}/{len(all_files)} ({100 * completed / len(all_files):.1f}%) | "
                        f"Rate: {rate:.1f} files/sec | ETA: {eta / 60:.1f} min"
                    )

            except Exception as e:
                print(f"  Error processing {file_path}: {e}")
                errors += 1

    # Save results for each chat
    print(f"\nSaving transcripts...")
    for chat_name in results_by_chat:
        # If resuming, merge with existing
        if args.resume:
            json_path = OUTPUT_DIR / chat_name / "transcripts.json"
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                results_by_chat[chat_name] = old_data + results_by_chat[chat_name]

        save_transcripts(chat_name, results_by_chat[chat_name])
        print(f"  Saved: {chat_name} ({len(results_by_chat[chat_name])} files)")

    # Final summary
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n{'=' * 60}")
    print(f"TRANSCRIPTION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Total files: {completed}")
    print(f"Errors: {errors}")
    print(f"Time: {elapsed / 60:.1f} minutes")
    print(f"Rate: {completed / elapsed:.2f} files/sec")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    # Required for Windows multiprocessing
    import multiprocessing

    multiprocessing.freeze_support()
    main()
