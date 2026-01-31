#!/usr/bin/env python3
"""
Re-transcribe files with quality issues using a better model.

Usage:
    python retranscribe_bad.py --model small
    python retranscribe_bad.py --model medium --chat Laura
"""

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

# FFmpeg path
os.environ["PATH"] = (
    r"C:\Users\Alejandro\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin"
    + os.pathsep
    + os.environ.get("PATH", "")
)

BASE_DIR = Path(__file__).parent.parent
TRANSCRIPTS_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "voice_note_transcripts"
SOURCE_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "whatsapp transcripts"
ISSUES_FILE = BASE_DIR / "SOURCE_OF_TRUTH" / "RETRANSCRIBE_LIST.txt"


def check_quality(text: str) -> list[str]:
    """Check for quality issues."""
    problems = []

    asian_chars = len(
        re.findall(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]", text)
    )
    if asian_chars > 3:
        problems.append(f"asian_chars:{asian_chars}")

    words = len(text.split())
    if words < 3:
        problems.append(f"too_short:{words}w")

    if re.search(r"(.{15,})\1{2,}", text):
        problems.append("repetitive_phrase")

    if re.search(r"\b(\w+)\s+\1\s+\1\s+\1\b", text.lower()):
        problems.append("word_repetition")

    if re.search(r"\.{5,}|\?{4,}|!{4,}", text):
        problems.append("punct_spam")

    return problems


def parse_date(filename: str) -> str | None:
    """Extract date from filename."""
    try:
        parts = filename.split("-")
        if len(parts) >= 2 and len(parts[1]) == 8:
            return f"{parts[1][:4]}-{parts[1][4:6]}-{parts[1][6:8]}"
    except Exception:
        pass
    return None


def load_issues(chat_filter: str | None = None) -> dict[str, list[str]]:
    """Load list of files with issues."""
    issues = {}

    if ISSUES_FILE.exists():
        with open(ISSUES_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if "/" in line:
                    chat, filename = line.split("/", 1)
                    if chat_filter and chat_filter.lower() not in chat.lower():
                        continue
                    issues.setdefault(chat, []).append(filename)

    return issues


def retranscribe(
    chat_name: str, files: list[str], model_name: str = "small", language: str = "es"
):
    """Re-transcribe specific files with better model."""
    import gc
    import torch
    import whisper

    # Find source directory
    source_dir = None
    for d in SOURCE_DIR.iterdir():
        if chat_name.lower() in d.name.lower():
            source_dir = d
            break

    if not source_dir:
        print(f"Source directory not found for {chat_name}")
        return

    # Load existing transcripts
    json_path = TRANSCRIPTS_DIR / chat_name / "transcripts.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        results = {item["file"]: item for item in data}
    else:
        results = {}

    # Filter to files that exist
    files_to_process = []
    for filename in files:
        filepath = source_dir / filename
        if filepath.exists():
            files_to_process.append(filepath)
        else:
            print(f"  Warning: {filename} not found")

    if not files_to_process:
        print(f"No files to process for {chat_name}")
        return

    print(f"\n{'=' * 60}")
    print(f"Re-transcribing {len(files_to_process)} files from {chat_name}")
    print(f"Model: {model_name}")
    print(f"{'=' * 60}\n")

    # Load model
    print(f"Loading Whisper '{model_name}'...")
    model = whisper.load_model(model_name)
    print("Model ready.\n")

    improved = 0
    still_bad = 0

    for i, filepath in enumerate(files_to_process):
        filename = filepath.name
        old_text = results.get(filename, {}).get("text", "")
        old_problems = check_quality(old_text) if old_text else ["no_previous"]

        try:
            # Use fp16 for GPU, but small/medium models need more VRAM
            use_fp16 = model_name in ("tiny", "base", "small")
            r = model.transcribe(
                str(filepath), language=language, fp16=use_fp16, verbose=False
            )
            new_text = r["text"]
            if isinstance(new_text, str):
                new_text = new_text.strip()
            else:
                new_text = str(new_text).strip() if new_text else ""

            new_problems = check_quality(new_text)

            # Update if improved (fewer problems)
            if len(new_problems) < len(old_problems):
                results[filename] = {
                    "file": filename,
                    "date": parse_date(filename),
                    "text": new_text,
                    "duration": r.get("duration"),
                    "success": True,
                    "retranscribed": True,
                    "model": model_name,
                }
                improved += 1
                status = "IMPROVED"
            elif len(new_problems) == 0 and len(old_problems) > 0:
                results[filename] = {
                    "file": filename,
                    "date": parse_date(filename),
                    "text": new_text,
                    "duration": r.get("duration"),
                    "success": True,
                    "retranscribed": True,
                    "model": model_name,
                }
                improved += 1
                status = "FIXED"
            else:
                still_bad += 1
                status = "STILL_BAD"

            print(f"  [{i + 1}/{len(files_to_process)}] {filename}: {status}")
            print(f"      Old: {old_problems} -> New: {new_problems}")

        except Exception as e:
            print(f"  [{i + 1}/{len(files_to_process)}] {filename}: ERROR - {e}")
            still_bad += 1

        # Memory cleanup
        if (i + 1) % 10 == 0:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    # Save updated results
    out_dir = TRANSCRIPTS_DIR / chat_name
    out_dir.mkdir(parents=True, exist_ok=True)

    items = list(results.values())
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"\nResults: {improved} improved, {still_bad} still have issues")
    print(f"Saved to: {json_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Re-transcribe problematic files with better model"
    )
    parser.add_argument(
        "--model", default="small", help="Whisper model: small, medium, large"
    )
    parser.add_argument("--chat", default=None, help="Filter to specific chat")
    parser.add_argument("--language", default="es", help="Language code")
    args = parser.parse_args()

    issues = load_issues(args.chat)

    if not issues:
        print("No issues found. Run check_quality.py first.")
        return

    print(f"Found issues in {len(issues)} chats:")
    for chat, files in sorted(issues.items()):
        print(f"  {chat}: {len(files)} files")
    print()

    for chat, files in sorted(issues.items(), key=lambda x: len(x[1])):
        retranscribe(chat, files, args.model, args.language)


if __name__ == "__main__":
    main()
