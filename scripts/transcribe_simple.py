#!/usr/bin/env python3
"""Simple single-threaded transcription for one chat."""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# FFmpeg path
os.environ["PATH"] = (
    r"C:\Users\Alejandro\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin"
    + os.pathsep
    + os.environ.get("PATH", "")
)

BASE_DIR = Path(__file__).parent.parent
TRANSCRIPTS_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "whatsapp transcripts"
OUTPUT_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "voice_note_transcripts"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("chat", help="Chat folder name (e.g., Laura, Magali_Carreras)")
    parser.add_argument("--model", default="tiny")
    parser.add_argument("--language", default="es")
    args = parser.parse_args()

    # Find chat folder
    chat_dir = None
    for d in TRANSCRIPTS_DIR.iterdir():
        if args.chat.lower() in d.name.lower():
            chat_dir = d
            break

    if not chat_dir:
        print(f"Chat '{args.chat}' not found")
        return

    files = sorted(chat_dir.glob("*.opus"))
    if not files:
        print(f"No .opus files in {chat_dir}")
        return

    print(f"Processing {chat_dir.name}: {len(files)} files")

    # Load model
    import whisper

    print(f"Loading Whisper '{args.model}'...")
    model = whisper.load_model(args.model)
    print("Model ready.")

    results = []
    start = datetime.now()

    for i, f in enumerate(files):
        try:
            r = model.transcribe(
                str(f), language=args.language, fp16=False, verbose=False
            )

            # Parse date
            date = None
            try:
                parts = f.name.split("-")
                if len(parts) >= 2 and len(parts[1]) == 8:
                    date = f"{parts[1][:4]}-{parts[1][4:6]}-{parts[1][6:8]}"
            except Exception:
                pass

            results.append(
                {
                    "file": f.name,
                    "date": date,
                    "text": r["text"].strip(),
                    "duration": r.get("duration"),
                    "success": True,
                }
            )
        except Exception as e:
            results.append(
                {
                    "file": f.name,
                    "error": str(e),
                    "success": False,
                }
            )

        if (i + 1) % 50 == 0 or i == len(files) - 1:
            elapsed = (datetime.now() - start).total_seconds()
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (len(files) - i - 1) / rate / 60 if rate > 0 else 0
            print(
                f"  {i + 1}/{len(files)} ({100 * (i + 1) / len(files):.1f}%) | {rate:.2f}/sec | ETA: {eta:.1f}m"
            )

    # Save
    out_dir = OUTPUT_DIR / chat_dir.name
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "transcripts.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Markdown
    by_date = {}
    for r in results:
        d = r.get("date") or "unknown"
        by_date.setdefault(d, []).append(r)

    with open(out_dir / "transcripts.md", "w", encoding="utf-8") as f:
        f.write(f"# Voice Notes: {chat_dir.name}\n\n")
        f.write(f"> {len(results)} files | {datetime.now():%Y-%m-%d %H:%M}\n\n---\n\n")
        for date in sorted(by_date):
            f.write(f"## {date}\n\n")
            for r in sorted(by_date[date], key=lambda x: x["file"]):
                f.write(f"### {r['file']}\n\n")
                if r.get("text"):
                    f.write(f"{r['text']}\n\n")
                elif r.get("error"):
                    f.write(f"*Error: {r['error']}*\n\n")
            f.write("---\n\n")

    elapsed = (datetime.now() - start).total_seconds()
    errors = sum(1 for r in results if not r.get("success"))
    print(f"\nDone: {len(results)} files in {elapsed / 60:.1f}m ({errors} errors)")
    print(f"Saved to: {out_dir}")


if __name__ == "__main__":
    main()
