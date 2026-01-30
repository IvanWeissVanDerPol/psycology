#!/usr/bin/env python3
"""
Voice Note Transcript Analysis Script for Ivan's Psychology Repository

Analyzes transcribed voice notes for emotional patterns, key themes,
and psychological insights.

Usage:
    python analyze_transcripts.py [--chat Laura] [--output analysis.md]
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configuration
BASE_DIR = Path(__file__).parent.parent
TRANSCRIPTS_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "voice_note_transcripts"
OUTPUT_DIR = BASE_DIR / "SOURCE_OF_TRUTH"


# Emotional/psychological keyword patterns (Spanish)
EMOTIONAL_PATTERNS = {
    "vulnerability": [
        r"\bmiedo\b",
        r"\basust",
        r"\bnervi",
        r"\bansi",
        r"\bpreocup",
        r"\btriste\b",
        r"\bllor",
        r"\bdolor",
        r"\bmal\b",
        r"\bsol[oa]\b",
        r"\bcansa",
        r"\bagota",
        r"\bestres",
        r"\bpresion",
    ],
    "needs_expression": [
        r"\bnecesit",
        r"\bquier[oa]\b",
        r"\bextrañ",
        r"\bfalta\b",
        r"\bayuda",
        r"\bapoy",
        r"\bcompañ",
    ],
    "self_deprecation": [
        r"\bpesad[oa]\b",
        r"\bmolest",
        r"\bculpa\b",
        r"\berror\b",
        r"\bmal[oa]\b",
        r"\btont[oa]\b",
        r"\bestúpid",
    ],
    "positive_affect": [
        r"\bfeliz\b",
        r"\bconten",
        r"\bbien\b",
        r"\bgenial\b",
        r"\balegr",
        r"\bdivert",
        r"\bchilo\b",
        r"\blindo\b",
    ],
    "deflection_minimizing": [
        r"\bno importa\b",
        r"\bno pasa nada\b",
        r"\btranqui",
        r"\bno te preocup",
        r"\bnada más\b",
        r"\bsolo\b",
    ],
    "service_offering": [
        r"\bte ayudo\b",
        r"\bpuedo hacer\b",
        r"\bsi necesit",
        r"\bavís[ae]me\b",
        r"\bcuent[ae] conmigo\b",
    ],
}

# Relationship-specific context
RELATIONSHIP_CONTEXT = {
    "Laura": "romantic_partner",
    "Lourdes_Youko_Kurama": "fwb",
    "Magali_Carreras": "close_friend_fixer",
    "Jonatan_Verdun": "male_friend_fixer",
    "Ara_Nunez_Poli": "balanced_friend",
    "Cookie": "breakthrough_friend",
}


def load_transcripts(chat_filter: Optional[str] = None) -> dict[str, list[dict]]:
    """Load all transcripts from JSON files."""
    transcripts = {}

    for chat_dir in TRANSCRIPTS_DIR.iterdir():
        if not chat_dir.is_dir():
            continue

        chat_name = chat_dir.name
        if chat_filter and chat_filter.lower() not in chat_name.lower():
            continue

        json_path = chat_dir / "transcripts.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Filter out errors
                valid = [t for t in data if t.get("text") and not t.get("error")]
                if valid:
                    transcripts[chat_name] = valid

    return transcripts


def analyze_emotional_patterns(text: str) -> dict[str, int]:
    """Count emotional pattern matches in text."""
    results = {}
    text_lower = text.lower()

    for category, patterns in EMOTIONAL_PATTERNS.items():
        count = sum(len(re.findall(p, text_lower)) for p in patterns)
        if count > 0:
            results[category] = count

    return results


def analyze_chat(chat_name: str, transcripts: list[dict]) -> dict:
    """Analyze all transcripts for a single chat."""
    total_words = 0
    total_duration = 0
    pattern_counts = Counter()
    by_date = defaultdict(list)

    for t in transcripts:
        text = t.get("text", "")
        if not text:
            continue

        # Word count
        words = len(text.split())
        total_words += words

        # Duration
        if t.get("duration"):
            total_duration += t["duration"]

        # Emotional patterns
        patterns = analyze_emotional_patterns(text)
        for category, count in patterns.items():
            pattern_counts[category] += count

        # Group by date
        date = t.get("date", "unknown")
        by_date[date].append(
            {
                "file": t["file"],
                "text": text,
                "words": words,
                "patterns": patterns,
            }
        )

    return {
        "chat_name": chat_name,
        "relationship_type": RELATIONSHIP_CONTEXT.get(chat_name, "unknown"),
        "total_files": len(transcripts),
        "total_words": total_words,
        "total_duration_sec": total_duration,
        "pattern_counts": dict(pattern_counts),
        "by_date": dict(by_date),
        "date_range": (min(by_date.keys()), max(by_date.keys())) if by_date else None,
    }


def find_notable_quotes(
    transcripts: list[dict], patterns_to_find: list[str]
) -> list[dict]:
    """Find quotes containing specific emotional patterns."""
    notable = []

    for t in transcripts:
        text = t.get("text", "")
        if not text:
            continue

        text_lower = text.lower()
        matched_patterns = []

        for pattern_name in patterns_to_find:
            if pattern_name in EMOTIONAL_PATTERNS:
                for regex in EMOTIONAL_PATTERNS[pattern_name]:
                    if re.search(regex, text_lower):
                        matched_patterns.append(pattern_name)
                        break

        if matched_patterns:
            notable.append(
                {
                    "file": t["file"],
                    "date": t.get("date"),
                    "text": text[:500] + ("..." if len(text) > 500 else ""),
                    "patterns": list(set(matched_patterns)),
                }
            )

    return notable


def generate_report(analyses: dict[str, dict]) -> str:
    """Generate markdown analysis report."""
    lines = [
        "# Voice Note Analysis Report",
        "",
        f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> Total chats analyzed: {len(analyses)}",
        "",
        "---",
        "",
        "## Summary Statistics",
        "",
        "| Chat | Files | Words | Duration | Top Pattern |",
        "|------|-------|-------|----------|-------------|",
    ]

    for chat_name, analysis in sorted(analyses.items()):
        files = analysis["total_files"]
        words = analysis["total_words"]
        duration = analysis["total_duration_sec"]
        duration_str = f"{duration / 60:.0f}m" if duration else "N/A"

        top_pattern = "none"
        if analysis["pattern_counts"]:
            top_pattern = max(
                analysis["pattern_counts"], key=analysis["pattern_counts"].get
            )

        lines.append(
            f"| {chat_name} | {files} | {words:,} | {duration_str} | {top_pattern} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## Emotional Pattern Distribution",
            "",
        ]
    )

    # Aggregate patterns across all chats
    all_patterns = Counter()
    for analysis in analyses.values():
        all_patterns.update(analysis["pattern_counts"])

    lines.append("| Pattern | Count | Interpretation |")
    lines.append("|---------|-------|----------------|")

    pattern_interpretations = {
        "vulnerability": "Direct emotional expression (rare for Ivan)",
        "needs_expression": "Stating needs/wants (core therapeutic target)",
        "self_deprecation": "Echoes of 'pesado' wound",
        "positive_affect": "Moments of genuine positive emotion",
        "deflection_minimizing": "The Mask in action - minimizing concerns",
        "service_offering": "The Fixer pattern - offering help",
    }

    for pattern, count in all_patterns.most_common():
        interp = pattern_interpretations.get(pattern, "")
        lines.append(f"| {pattern} | {count} | {interp} |")

    # Per-chat detailed analysis
    lines.extend(
        [
            "",
            "---",
            "",
            "## Per-Chat Analysis",
            "",
        ]
    )

    for chat_name, analysis in sorted(analyses.items()):
        rel_type = analysis["relationship_type"]
        lines.extend(
            [
                f"### {chat_name} ({rel_type})",
                "",
                f"**Files:** {analysis['total_files']}  ",
                f"**Words:** {analysis['total_words']:,}  ",
            ]
        )

        if analysis["date_range"]:
            lines.append(
                f"**Date Range:** {analysis['date_range'][0]} to {analysis['date_range'][1]}  "
            )

        if analysis["pattern_counts"]:
            lines.append("")
            lines.append("**Pattern Distribution:**")
            for pattern, count in sorted(
                analysis["pattern_counts"].items(), key=lambda x: -x[1]
            ):
                lines.append(f"- {pattern}: {count}")

        lines.extend(["", "---", ""])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze voice note transcripts")
    parser.add_argument("--chat", default=None, help="Filter to specific chat")
    parser.add_argument(
        "--output", default="VOICE_NOTE_ANALYSIS.md", help="Output filename"
    )
    parser.add_argument(
        "--find-quotes", action="store_true", help="Find notable quotes"
    )

    args = parser.parse_args()

    print(f"Loading transcripts from: {TRANSCRIPTS_DIR}")
    transcripts = load_transcripts(args.chat)

    if not transcripts:
        print("No transcripts found!")
        return

    print(f"Found transcripts for {len(transcripts)} chats")

    # Analyze each chat
    analyses = {}
    for chat_name, chat_transcripts in transcripts.items():
        print(f"  Analyzing {chat_name}...")
        analyses[chat_name] = analyze_chat(chat_name, chat_transcripts)

    # Generate report
    report = generate_report(analyses)

    output_path = OUTPUT_DIR / args.output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {output_path}")

    # Find notable quotes if requested
    if args.find_quotes:
        print("\nFinding notable quotes...")
        all_quotes = {}
        for chat_name, chat_transcripts in transcripts.items():
            quotes = find_notable_quotes(
                chat_transcripts,
                ["vulnerability", "needs_expression", "self_deprecation"],
            )
            if quotes:
                all_quotes[chat_name] = quotes
                print(f"\n{chat_name}: {len(quotes)} notable quotes found")
                for q in quotes[:3]:  # Show first 3
                    # Clean text for console output (handle unicode issues)
                    clean_text = (
                        q["text"][:100].encode("ascii", "replace").decode("ascii")
                    )
                    print(f"  [{q['date']}] {q['patterns']}: {clean_text}...")

        # Save quotes to file
        quotes_path = OUTPUT_DIR / "NOTABLE_QUOTES.md"
        with open(quotes_path, "w", encoding="utf-8") as f:
            f.write("# Notable Quotes from Voice Notes\n\n")
            f.write(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(
                "These quotes contain expressions of vulnerability, needs, or self-deprecation.\n\n---\n\n"
            )

            for chat_name, quotes in sorted(all_quotes.items()):
                rel_type = RELATIONSHIP_CONTEXT.get(chat_name, "unknown")
                f.write(f"## {chat_name} ({rel_type})\n\n")
                f.write(f"**{len(quotes)} notable quotes**\n\n")

                for q in quotes:
                    f.write(f"### {q['file']} ({q['date']})\n")
                    f.write(f"**Patterns:** {', '.join(q['patterns'])}\n\n")
                    f.write(f"> {q['text']}\n\n")

                f.write("---\n\n")

        print(f"\nQuotes saved to: {quotes_path}")


if __name__ == "__main__":
    main()
