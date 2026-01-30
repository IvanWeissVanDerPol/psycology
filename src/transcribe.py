#!/usr/bin/env python3
"""
Unified Voice Note Transcription System

A comprehensive CLI tool for transcribing WhatsApp voice notes with multiple modes:
- single: Process one chat
- parallel: Process multiple chats with multiprocessing
- all: Process all chats
- resume: Resume interrupted transcription
- retranscribe: Re-transcribe low-quality files
- check: Check transcript quality
- status: Show transcription status

Usage:
    python transcribe.py single Laura --model base
    python transcribe.py parallel --workers 4
    python transcribe.py all
    python transcribe.py resume Laura
    python transcribe.py check
    python transcribe.py status
"""

from __future__ import annotations

import argparse
import gc
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from transcription import (
    config,
    get_model,
    transcribe_file,
    clear_model_cache,
    save_transcripts,
    load_transcripts,
    get_already_transcribed,
    find_chat_directory,
    get_audio_files,
    check_quality,
    setup_logging,
)

logger = setup_logging(__name__)


def cmd_single(args: argparse.Namespace) -> int:
    """Transcribe a single chat."""
    chat_name = args.chat

    # Find chat directory
    chat_dir = find_chat_directory(config.paths.transcripts_source, chat_name)
    if not chat_dir:
        logger.error(f"Chat '{chat_name}' not found")
        return 1

    # Get audio files
    files = get_audio_files(chat_dir)
    if not files:
        logger.error(f"No audio files found in {chat_dir}")
        return 1

    logger.info(f"Processing {chat_dir.name}: {len(files)} files")

    # Load model
    model = get_model(args.model)
    logger.info(f"Model '{args.model}' loaded")

    # Process files
    results = []
    start_time = datetime.now()

    for i, file_path in enumerate(files):
        result = transcribe_file(
            file_path,
            model_name=args.model,
            language=args.language,
            validate_quality=True,
        )
        results.append(result)

        # Progress update
        if (i + 1) % 50 == 0 or i == len(files) - 1:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (len(files) - i - 1) / rate / 60 if rate > 0 else 0
            logger.info(
                f"Progress: {i + 1}/{len(files)} ({100 * (i + 1) / len(files):.1f}%) | "
                f"Rate: {rate:.2f}/sec | ETA: {eta:.1f}m"
            )

    # Save results
    json_path, md_path = save_transcripts(chat_dir.name, results)
    if json_path:
        logger.info(f"Saved: {json_path}")
    if md_path:
        logger.info(f"Saved: {md_path}")

    # Summary
    errors = sum(1 for r in results if not r.get("success"))
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"Complete: {len(results)} files in {elapsed / 60:.1f}m ({errors} errors)"
    )

    return 0 if errors == 0 else 1


def cmd_parallel(args: argparse.Namespace) -> int:
    """Transcribe using multiple workers."""
    # Find all chats
    all_chats = {}
    for chat_dir in config.paths.transcripts_source.iterdir():
        if chat_dir.is_dir():
            files = get_audio_files(chat_dir)
            if files:
                all_chats[chat_dir.name] = files

    if not all_chats:
        logger.error("No chats found")
        return 1

    # Filter if specified
    if args.chat:
        all_chats = {
            k: v for k, v in all_chats.items() if args.chat.lower() in k.lower()
        }

    total_files = sum(len(f) for f in all_chats.values())
    logger.info(f"Found {total_files} files across {len(all_chats)} chats")

    # Collect files to process
    files_to_process = []
    for chat_name, files in all_chats.items():
        if args.resume:
            done = get_already_transcribed(chat_name)
            files = [f for f in files if f.name not in done]
            if not files:
                logger.info(f"{chat_name}: all files already transcribed")
                continue
        for f in files:
            files_to_process.append((chat_name, f))

    if not files_to_process:
        logger.info("All files already transcribed!")
        return 0

    logger.info(
        f"Processing {len(files_to_process)} files with {args.workers} workers..."
    )

    # Process with process pool
    results_by_chat: dict[str, list] = {chat: [] for chat in all_chats.keys()}
    start_time = datetime.now()
    completed = 0
    errors = 0

    # Prepare work items
    work_items = [
        (str(f), args.model, args.language, chat) for chat, f in files_to_process
    ]

    def process_single(args_tuple):
        """Process a single file (for pool)."""
        file_path, model_name, language, chat_name = args_tuple
        result = transcribe_file(
            Path(file_path),
            model_name=model_name,
            language=language,
        )
        return chat_name, result

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        future_to_item = {
            executor.submit(process_single, item): item for item in work_items
        }

        for future in as_completed(future_to_item):
            try:
                chat_name, result = future.result()
                results_by_chat[chat_name].append(result)
                completed += 1

                if not result.get("success"):
                    errors += 1
                    logger.warning(f"Failed: {result.get('file')}")

                # Progress update
                if completed % 50 == 0 or completed == len(files_to_process):
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = completed / elapsed if elapsed > 0 else 0
                    eta = (
                        (len(files_to_process) - completed) / rate / 60
                        if rate > 0
                        else 0
                    )
                    logger.info(
                        f"Progress: {completed}/{len(files_to_process)} "
                        f"({100 * completed / len(files_to_process):.1f}%) | "
                        f"Rate: {rate:.1f}/sec | ETA: {eta:.1f}m"
                    )

            except Exception as e:
                logger.error(f"Worker error: {e}")
                errors += 1

    # Save results
    logger.info("Saving transcripts...")
    for chat_name, results in results_by_chat.items():
        if results:
            if args.resume:
                # Merge with existing
                existing = load_transcripts(chat_name)
                existing_files = {e["file"] for e in existing}
                new_results = [r for r in results if r["file"] not in existing_files]
                results = existing + new_results

            save_transcripts(chat_name, results)
            logger.info(f"Saved {chat_name}: {len(results)} files")

    # Final summary
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Complete: {completed} files in {elapsed / 60:.1f}m ({errors} errors)")

    return 0 if errors == 0 else 1


def cmd_all(args: argparse.Namespace) -> int:
    """Process all chats."""
    # Find all chats
    chats = []
    for chat_dir in config.paths.transcripts_source.iterdir():
        if chat_dir.is_dir():
            files = get_audio_files(chat_dir)
            if files:
                chats.append((chat_dir.name, len(files)))

    if not chats:
        logger.error("No chats found")
        return 1

    # Sort by size (smallest first for quick wins)
    chats.sort(key=lambda x: x[1])

    logger.info(f"Will process {len(chats)} chats (smallest first):")
    for name, count in chats:
        logger.info(f"  {name}: {count} files")

    # Process each chat
    total_errors = 0
    for chat_name, _ in chats:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Processing: {chat_name}")
        logger.info("=" * 60)

        # Create args for single command
        single_args = argparse.Namespace(
            chat=chat_name,
            model=args.model,
            language=args.language,
        )

        result = cmd_single(single_args)
        total_errors += result

        # Brief pause between chats
        import time

        time.sleep(2)

    logger.info(f"\n{'=' * 60}")
    logger.info(f"ALL CHATS COMPLETE ({total_errors} total errors)")
    logger.info("=" * 60)

    return total_errors


def cmd_resume(args: argparse.Namespace) -> int:
    """Resume transcription for a chat."""
    chat_name = args.chat

    # Load existing progress
    existing = get_already_transcribed(chat_name)
    logger.info(f"Found {len(existing)} already transcribed files")

    # Set resume flag and delegate to single
    args.resume = True
    return cmd_single(args)


def cmd_retranscribe(args: argparse.Namespace) -> int:
    """Re-transcribe low-quality files."""
    # Load quality issues
    import json

    issues_file = config.paths.source_of_truth / "RETRANSCRIBE_LIST.txt"

    if not issues_file.exists():
        logger.error("No retranscribe list found. Run 'check' first.")
        return 1

    # Parse issues file
    issues: dict[str, list[str]] = {}
    with open(issues_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "/" in line:
                chat, filename = line.split("/", 1)
                issues.setdefault(chat, []).append(filename)

    if not issues:
        logger.info("No files need re-transcription")
        return 0

    total = sum(len(f) for f in issues.values())
    logger.info(f"Re-transcribing {total} files with quality issues")

    # Use turbo model for better quality
    model = get_model("turbo")
    improved = 0
    still_bad = 0

    for chat_name, files in issues.items():
        logger.info(f"\nProcessing {chat_name}: {len(files)} files")

        # Load existing transcripts
        existing = {t["file"]: t for t in load_transcripts(chat_name)}
        results = dict(existing)  # Start with existing

        # Find source files
        chat_dir = find_chat_directory(config.paths.transcripts_source, chat_name)
        if not chat_dir:
            logger.warning(f"Source not found: {chat_name}")
            continue

        for i, filename in enumerate(files):
            file_path = chat_dir / filename
            if not file_path.exists():
                logger.warning(f"  File not found: {filename}")
                continue

            # Get old quality
            old_text = existing.get(filename, {}).get("text", "")
            old_quality = check_quality(old_text)

            # Re-transcribe
            try:
                result = transcribe_file(
                    file_path,
                    model_name="turbo",
                    language=args.language,
                )

                new_quality = check_quality(result.get("text", ""))

                # Update if better
                results[filename] = result

                if len(new_quality.problems) < len(old_quality.problems):
                    improved += 1
                    logger.info(f"  [{i + 1}/{len(files)}] {filename}: IMPROVED")
                elif new_quality.is_valid:
                    improved += 1
                    logger.info(f"  [{i + 1}/{len(files)}] {filename}: FIXED")
                else:
                    still_bad += 1
                    logger.info(f"  [{i + 1}/{len(files)}] {filename}: STILL_BAD")

            except Exception as e:
                logger.error(f"  [{i + 1}/{len(files)}] {filename}: ERROR - {e}")
                still_bad += 1

            # Memory cleanup
            if (i + 1) % 20 == 0:
                gc.collect()

        # Save updated transcripts
        save_transcripts(chat_name, list(results.values()))

    logger.info(f"\nComplete: {improved} improved, {still_bad} still have issues")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Check transcript quality."""
    import json
    from collections import Counter

    issues = []
    total_checked = 0

    for chat_dir in config.paths.transcripts_output.iterdir():
        if not chat_dir.is_dir():
            continue

        json_path = chat_dir / "transcripts.json"
        if not json_path.exists():
            continue

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load {json_path}: {e}")
            continue

        for t in data:
            if not t.get("success") or not t.get("text"):
                continue

            total_checked += 1
            quality = check_quality(t["text"])

            if not quality.is_valid:
                issues.append(
                    {
                        "chat": chat_dir.name,
                        "file": t["file"],
                        "date": t.get("date"),
                        "problems": quality.problems,
                    }
                )

    # Sort by severity
    issues.sort(key=lambda x: (-len(x["problems"]), x["chat"], x["file"]))

    # Generate report
    logger.info(f"Checked {total_checked} transcripts")
    logger.info(
        f"Found {len(issues)} with quality issues "
        f"({100 * len(issues) / max(total_checked, 1):.1f}%)"
    )

    # Save retranscribe list
    retranscribe_list = config.paths.source_of_truth / "RETRANSCRIBE_LIST.txt"
    with open(retranscribe_list, "w", encoding="utf-8") as f:
        for issue in issues:
            f.write(f"{issue['chat']}/{issue['file']}\n")

    logger.info(f"Retranscribe list saved to: {retranscribe_list}")

    return 0 if not issues else 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show transcription status."""
    import json

    status = {}
    total_done = 0
    total_files = 0

    for source_dir in config.paths.transcripts_source.iterdir():
        if not source_dir.is_dir():
            continue

        chat_name = source_dir.name
        opus_files = list(source_dir.glob("*.opus"))
        total = len(opus_files)

        if total == 0:
            continue

        # Check transcripts
        json_path = config.paths.transcripts_output / chat_name / "transcripts.json"
        success = 0
        failed = 0

        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                success = sum(1 for t in data if t.get("success"))
                failed = sum(1 for t in data if not t.get("success"))
            except (OSError, json.JSONDecodeError):
                pass

        remaining = total - success
        status[chat_name] = {
            "total": total,
            "success": success,
            "failed": failed,
            "remaining": remaining,
        }
        total_done += success
        total_files += total

    # Print table
    print("\n" + "=" * 70)
    print(
        f"{'Chat':<25} {'Done':<8} {'Failed':<8} {'Total':<8} {'%':<8} {'Status':<10}"
    )
    print("=" * 70)

    for chat, s in sorted(status.items(), key=lambda x: x[1]["remaining"]):
        pct = 100 * s["success"] / s["total"] if s["total"] > 0 else 0
        if s["remaining"] == 0:
            status_str = "✓ DONE"
        elif s["success"] > 0:
            status_str = "⏳ PARTIAL"
        else:
            status_str = "○ PENDING"
        print(
            f"{chat:<25} {s['success']:<8} {s['failed']:<8} {s['total']:<8} "
            f"{pct:>6.1f}%  {status_str}"
        )

    print("=" * 70)
    overall_pct = 100 * total_done / total_files if total_files > 0 else 0
    print(
        f"{'TOTAL':<25} {total_done:<8} {'':<8} {total_files:<8} {overall_pct:>6.1f}%"
    )
    print("=" * 70 + "\n")

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="transcribe",
        description="Unified voice note transcription system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s single Laura --model base
    %(prog)s parallel --workers 4 --resume
    %(prog)s all --model small
    %(prog)s resume Laura
    %(prog)s retranscribe
    %(prog)s check
    %(prog)s status
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large", "turbo"],
        help="Whisper model to use (default: base)",
    )
    common_parser.add_argument(
        "--language", default="es", help="Language code (default: es)"
    )

    # Single command
    single_parser = subparsers.add_parser(
        "single", parents=[common_parser], help="Transcribe a single chat"
    )
    single_parser.add_argument("chat", help="Chat name (e.g., Laura)")
    single_parser.add_argument(
        "--resume", action="store_true", help="Skip already transcribed files"
    )

    # Parallel command
    parallel_parser = subparsers.add_parser(
        "parallel", parents=[common_parser], help="Transcribe using multiple workers"
    )
    parallel_parser.add_argument(
        "--workers", type=int, default=4, help="Number of parallel workers (default: 4)"
    )
    parallel_parser.add_argument(
        "--resume", action="store_true", help="Skip already transcribed files"
    )
    parallel_parser.add_argument("--chat", help="Process only specific chat")

    # All command
    all_parser = subparsers.add_parser(
        "all", parents=[common_parser], help="Process all chats"
    )

    # Resume command
    resume_parser = subparsers.add_parser(
        "resume", parents=[common_parser], help="Resume transcription for a chat"
    )
    resume_parser.add_argument("chat", help="Chat name to resume")

    # Retranscribe command
    retranscribe_parser = subparsers.add_parser(
        "retranscribe", help="Re-transcribe low-quality files with turbo model"
    )
    retranscribe_parser.add_argument(
        "--language", default="es", help="Language code (default: es)"
    )

    # Check command
    subparsers.add_parser("check", help="Check transcript quality")

    # Status command
    subparsers.add_parser("status", help="Show transcription status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Validate config
    validation_issues = config.validate()
    if validation_issues:
        logger.error("Configuration issues found:")
        for issue in validation_issues:
            logger.error(f"  - {issue}")
        return 1

    # Dispatch to command handler
    commands = {
        "single": cmd_single,
        "parallel": cmd_parallel,
        "all": cmd_all,
        "resume": cmd_resume,
        "retranscribe": cmd_retranscribe,
        "check": cmd_check,
        "status": cmd_status,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
