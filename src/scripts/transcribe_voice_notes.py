#!/usr/bin/env python3
"""
Voice Note Transcription Script for Ivan's Psychology Repository

Uses OpenAI Whisper (local) to transcribe all WhatsApp voice notes.
Outputs structured transcripts organized by relationship and date.

Requirements:
    pip install openai-whisper torch tqdm

Usage:
    python transcribe_voice_notes.py [--model base] [--language es] [--chat Laura]

Models (speed vs accuracy tradeoff):
    - tiny:   ~1GB RAM, fastest, least accurate
    - base:   ~1GB RAM, fast, good for clear audio (RECOMMENDED)
    - small:  ~2GB RAM, balanced
    - medium: ~5GB RAM, better accuracy
    - large:  ~10GB RAM, best accuracy, slowest
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add common ffmpeg locations to PATH for Windows
FFMPEG_PATHS = [
    r"C:\Users\Alejandro\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin",
    r"C:\ffmpeg\bin",
    r"C:\Program Files\ffmpeg\bin",
]
for ffmpeg_path in FFMPEG_PATHS:
    if os.path.exists(ffmpeg_path):
        os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ.get("PATH", "")
        break

try:
    import whisper
    from tqdm import tqdm
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install openai-whisper torch tqdm")
    sys.exit(1)


# Configuration
BASE_DIR = Path(__file__).parent.parent
TRANSCRIPTS_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "whatsapp transcripts"
OUTPUT_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "voice_note_transcripts"


def get_voice_notes(chat_filter: Optional[str] = None) -> dict[str, list[Path]]:
    """Find all voice notes organized by chat folder."""
    voice_notes = {}

    for chat_dir in TRANSCRIPTS_DIR.iterdir():
        if not chat_dir.is_dir():
            continue

        chat_name = chat_dir.name

        # Apply filter if specified
        if chat_filter and chat_filter.lower() not in chat_name.lower():
            continue

        # Find all .opus files
        opus_files = sorted(chat_dir.glob("*.opus"))
        if opus_files:
            voice_notes[chat_name] = opus_files

    return voice_notes


def parse_date_from_filename(filename: str) -> Optional[str]:
    """Extract date from WhatsApp voice note filename.

    Formats:
        PTT-20240902-WA0017.opus -> 2024-09-02
        AUD-20250720-WA0031.opus -> 2025-07-20
    """
    try:
        # Extract the date portion (YYYYMMDD)
        parts = filename.split("-")
        if len(parts) >= 2:
            date_str = parts[1]
            if len(date_str) == 8:
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    except Exception:
        pass
    return None


def transcribe_file(model, file_path: Path, language: str = "es") -> dict:
    """Transcribe a single voice note file."""
    try:
        result = model.transcribe(
            str(file_path),
            language=language,
            fp16=False,  # Use FP32 for CPU compatibility
            verbose=False,
        )

        return {
            "file": file_path.name,
            "date": parse_date_from_filename(file_path.name),
            "text": result["text"].strip(),
            "language": result.get("language", language),
            "duration": result.get("duration"),
            "segments": [
                {"start": seg["start"], "end": seg["end"], "text": seg["text"].strip()}
                for seg in result.get("segments", [])
            ],
        }
    except Exception as e:
        return {
            "file": file_path.name,
            "date": parse_date_from_filename(file_path.name),
            "error": str(e),
            "text": None,
        }


def save_transcripts(chat_name: str, transcripts: list[dict], output_dir: Path):
    """Save transcripts to JSON and markdown files."""
    chat_output_dir = output_dir / chat_name
    chat_output_dir.mkdir(parents=True, exist_ok=True)

    # Save full JSON
    json_path = chat_output_dir / "transcripts.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(transcripts, f, ensure_ascii=False, indent=2)

    # Save readable markdown organized by date
    md_path = chat_output_dir / "transcripts.md"

    # Group by date
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
                    if t.get("duration"):
                        f.write(f"*Duration: {t['duration']:.1f}s*\n\n")
                else:
                    f.write("*[Empty or inaudible]*\n\n")
            f.write("---\n\n")

    return json_path, md_path


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe WhatsApp voice notes using local Whisper"
    )
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base)",
    )
    parser.add_argument(
        "--language",
        default="es",
        help="Primary language code (default: es for Spanish)",
    )
    parser.add_argument(
        "--chat", default=None, help="Filter to specific chat (e.g., 'Laura', 'Cookie')"
    )
    parser.add_argument(
        "--resume", action="store_true", help="Skip files that already have transcripts"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be transcribed without doing it",
    )

    args = parser.parse_args()

    # Find voice notes
    print(f"Scanning for voice notes in: {TRANSCRIPTS_DIR}")
    voice_notes = get_voice_notes(args.chat)

    if not voice_notes:
        print("No voice notes found!")
        return

    # Summary
    total = sum(len(files) for files in voice_notes.values())
    print(f"\nFound {total} voice notes across {len(voice_notes)} chats:\n")
    for chat, files in sorted(voice_notes.items(), key=lambda x: -len(x[1])):
        print(f"  {chat}: {len(files)} files")

    if args.dry_run:
        print("\n[DRY RUN] Would transcribe the above files.")
        return

    # Load model
    print(f"\nLoading Whisper model '{args.model}'...")
    model = whisper.load_model(args.model)
    print("Model loaded.\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Process each chat
    for chat_name, files in voice_notes.items():
        print(f"\n{'=' * 60}")
        print(f"Processing: {chat_name} ({len(files)} files)")
        print("=" * 60)

        # Check for existing transcripts if resuming
        existing = set()
        if args.resume:
            json_path = OUTPUT_DIR / chat_name / "transcripts.json"
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    existing = {t["file"] for t in json.load(f) if not t.get("error")}
                print(f"  Resuming: {len(existing)} already transcribed")

        transcripts = []
        files_to_process = [f for f in files if f.name not in existing]

        if not files_to_process:
            print("  All files already transcribed. Skipping.")
            continue

        # Transcribe with progress bar
        for file_path in tqdm(files_to_process, desc=f"  {chat_name}"):
            result = transcribe_file(model, file_path, args.language)
            transcripts.append(result)

        # If resuming, merge with existing
        if args.resume and existing:
            json_path = OUTPUT_DIR / chat_name / "transcripts.json"
            with open(json_path, "r", encoding="utf-8") as f:
                old_transcripts = json.load(f)
            transcripts = old_transcripts + transcripts

        # Save
        json_path, md_path = save_transcripts(chat_name, transcripts, OUTPUT_DIR)
        print(f"  Saved: {json_path}")
        print(f"  Saved: {md_path}")

        # Summary stats
        errors = sum(1 for t in transcripts if t.get("error"))
        if errors:
            print(f"  Warnings: {errors} files had errors")

    print(f"\n{'=' * 60}")
    print("TRANSCRIPTION COMPLETE")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
