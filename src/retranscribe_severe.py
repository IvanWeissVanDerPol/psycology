#!/usr/bin/env python3
"""
Re-transcribe severe quality issue files with turbo model.

This script targets the 6 files with multiple quality problems:
- 3+ problem types or Asian character hallucinations
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from transcription import config, get_model, transcribe_file, save_json
from transcription.utils.logging_utils import setup_logging
from transcription.utils.quality import check_quality

logger = setup_logging(__name__)

# Severe quality issues - files with multiple problems
SEVERE_ISSUES = [
    (
        "Jonatan_Verdun",
        "PTT-20250821-WA0069.opus",
        ["repetitive_phrase", "word_repetition", "english_mix:104"],
    ),
    ("Laura", "PTT-20250125-WA0002.opus", ["repetitive_phrase", "word_repetition"]),
    (
        "Lourdes_Youko_Kurama",
        "PTT-20251010-WA0081.opus",
        ["repetitive_phrase", "word_repetition"],
    ),
    (
        "Lourdes_Youko_Kurama",
        "PTT-20251025-WA0045.opus",
        ["word_repetition", "english_mix:41"],
    ),
    (
        "Magali_Carreras",
        "PTT-20231207-WA0036.opus",
        ["repetitive_phrase", "word_repetition"],
    ),
    ("Lourdes_Youko_Kurama", "PTT-20230922-WA0005.opus", ["asian_chars:4"]),
]


def retranscribe_severe_files():
    """Re-transcribe files with severe quality issues using turbo model."""
    logger.info("=" * 60)
    logger.info("RE-TRANSCRIBING SEVERE QUALITY ISSUE FILES")
    logger.info("=" * 60)

    # Load turbo model
    logger.info("Loading Whisper turbo model...")
    model = get_model("turbo")
    logger.info("Model loaded")

    improved_count = 0
    still_bad_count = 0

    for chat_name, filename, problems in SEVERE_ISSUES:
        logger.info(f"\nProcessing: {chat_name}/{filename}")
        logger.info(f"  Original problems: {problems}")

        # Find source file
        source_dir = config.paths.transcripts_source / chat_name
        source_file = source_dir / filename

        if not source_file.exists():
            logger.warning(f"  Source file not found: {source_file}")
            continue

        # Re-transcribe
        try:
            result = transcribe_file(
                source_file, model_name="turbo", language="es", validate_quality=True
            )

            new_text = result.get("text", "")
            new_quality = check_quality(new_text)

            # Load existing transcripts
            json_path = config.paths.transcripts_output / chat_name / "transcripts.json"
            if json_path.exists():
                import json

                with open(json_path, "r", encoding="utf-8") as f:
                    transcripts = json.load(f)

                # Find and update this file
                for t in transcripts:
                    if t["file"] == filename:
                        old_quality = check_quality(t.get("text", ""))

                        # Update with new result
                        t["text"] = new_text
                        t["quality_issues"] = new_quality.problems
                        t["retranscribed"] = True
                        t["model"] = "turbo"

                        # Check improvement
                        if len(new_quality.problems) < len(old_quality.problems):
                            improved_count += 1
                            logger.info(
                                f"  ✓ IMPROVED: {len(old_quality.problems)} -> {len(new_quality.problems)} problems"
                            )
                        elif new_quality.is_valid:
                            improved_count += 1
                            logger.info(f"  ✓ FIXED: Now clean")
                        else:
                            still_bad_count += 1
                            logger.info(f"  ✗ STILL BAD: {new_quality.problems}")
                        break

                # Save updated transcripts
                save_json(transcripts, json_path)
                logger.info(f"  Saved updated transcripts for {chat_name}")

        except Exception as e:
            logger.error(f"  Error re-transcribing: {e}")
            still_bad_count += 1

    logger.info("\n" + "=" * 60)
    logger.info(
        f"SUMMARY: {improved_count} improved, {still_bad_count} still have issues"
    )
    logger.info("=" * 60)

    return improved_count, still_bad_count


if __name__ == "__main__":
    improved, still_bad = retranscribe_severe_files()
    sys.exit(0 if still_bad == 0 else 1)
