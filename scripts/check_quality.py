#!/usr/bin/env python3
"""Check transcript quality and identify files needing re-transcription."""

import json
import re
from collections import Counter
from pathlib import Path

TRANSCRIPTS_DIR = (
    Path(__file__).parent.parent / "SOURCE_OF_TRUTH" / "voice_note_transcripts"
)
OUTPUT_DIR = Path(__file__).parent.parent / "SOURCE_OF_TRUTH"


def check_quality(text: str) -> list[str]:
    """Check for quality issues in transcript text."""
    problems = []

    # 1. Asian characters (Korean, Chinese, Japanese) - Whisper hallucination
    asian_chars = len(
        re.findall(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]", text)
    )
    if asian_chars > 3:
        problems.append(f"asian_chars:{asian_chars}")

    # 2. Very short
    words = len(text.split())
    if words < 3:
        problems.append(f"too_short:{words}w")

    # 3. Repetitive patterns (hallucination)
    if re.search(r"(.{15,})\1{2,}", text):
        problems.append("repetitive_phrase")

    # 4. Word repetition
    if re.search(r"\b(\w+)\s+\1\s+\1\s+\1\b", text.lower()):
        problems.append("word_repetition")

    # 5. Punctuation spam
    if re.search(r"\.{5,}|\?{4,}|!{4,}", text):
        problems.append("punct_spam")

    # 6. High English mix in Spanish audio
    english_words = len(
        re.findall(
            r"\b(the|and|but|with|for|this|that|what|have|from|are|was|were|been|will|would|could|should)\b",
            text.lower(),
        )
    )
    if english_words > 8:
        problems.append(f"english_mix:{english_words}")

    # 7. Gibberish indicators (high consonant clusters unusual for Spanish)
    gibberish = len(re.findall(r"[bcdfghjklmnpqrstvwxyz]{5,}", text.lower()))
    if gibberish > 3:
        problems.append(f"gibberish:{gibberish}")

    return problems


def main():
    issues = []
    total_checked = 0

    for chat_dir in TRANSCRIPTS_DIR.iterdir():
        if not chat_dir.is_dir():
            continue

        json_path = chat_dir / "transcripts.json"
        if not json_path.exists():
            continue

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for t in data:
            if not t.get("success") or not t.get("text"):
                continue

            total_checked += 1
            text = t["text"]
            problems = check_quality(text)

            if problems:
                issues.append(
                    {
                        "chat": chat_dir.name,
                        "file": t["file"],
                        "date": t.get("date"),
                        "problems": problems,
                        "text": text,
                    }
                )

    # Sort by severity (more problems = worse)
    issues.sort(key=lambda x: (-len(x["problems"]), x["chat"], x["file"]))

    # Write report
    output = OUTPUT_DIR / "QUALITY_ISSUES.md"
    with open(output, "w", encoding="utf-8") as f:
        f.write("# Transcript Quality Issues\n\n")
        f.write(
            f"> Checked {total_checked} transcripts, found {len(issues)} with issues ({100 * len(issues) / max(total_checked, 1):.1f}%)\n\n"
        )

        # Summary
        by_chat = Counter(i["chat"] for i in issues)
        f.write("## Summary by Chat\n\n")
        f.write("| Chat | Issues | Severity |\n|------|--------|----------|\n")
        for chat, count in by_chat.most_common():
            chat_issues = [i for i in issues if i["chat"] == chat]
            severe = sum(1 for i in chat_issues if len(i["problems"]) > 1)
            f.write(f"| {chat} | {count} | {severe} severe |\n")

        # Problem type summary
        all_problems = []
        for i in issues:
            all_problems.extend([p.split(":")[0] for p in i["problems"]])
        problem_counts = Counter(all_problems)

        f.write("\n## Problem Types\n\n")
        f.write(
            "| Problem | Count | Description |\n|---------|-------|-------------|\n"
        )
        descriptions = {
            "asian_chars": "Korean/Chinese/Japanese characters (Whisper hallucination)",
            "too_short": "Less than 3 words",
            "repetitive_phrase": "Same phrase repeated 3+ times",
            "word_repetition": "Same word 4+ times in a row",
            "punct_spam": "Excessive punctuation",
            "english_mix": "Many English words in Spanish audio",
            "gibberish": "Unusual consonant clusters (nonsense)",
        }
        for prob, count in problem_counts.most_common():
            desc = descriptions.get(prob, "")
            f.write(f"| {prob} | {count} | {desc} |\n")

        f.write("\n---\n\n")
        f.write("## Files to Re-transcribe\n\n")
        f.write(
            "These files should be re-transcribed with `--model small` or `--model medium`:\n\n"
        )

        # List by chat
        for chat in sorted(set(i["chat"] for i in issues)):
            chat_issues = [i for i in issues if i["chat"] == chat]
            f.write(f"### {chat} ({len(chat_issues)} files)\n\n")

            f.write("```\n")
            for i in chat_issues:
                probs = ", ".join(i["problems"])
                f.write(f"{i['file']}  # {probs}\n")
            f.write("```\n\n")

            # Show worst examples
            worst = [i for i in chat_issues if len(i["problems"]) > 1][:3]
            if worst:
                f.write("**Worst examples:**\n\n")
                for i in worst:
                    f.write(f"#### {i['file']}\n")
                    f.write(f"Problems: {', '.join(i['problems'])}\n\n")
                    f.write(
                        f"> {i['text'][:400]}{'...' if len(i['text']) > 400 else ''}\n\n"
                    )

            f.write("---\n\n")

    print(f"Checked {total_checked} transcripts")
    print(
        f"Found {len(issues)} with quality issues ({100 * len(issues) / max(total_checked, 1):.1f}%)"
    )
    print(f"\nBy chat:")
    for chat, count in by_chat.most_common():
        print(f"  {chat}: {count}")
    print(f"\nReport saved to: {output}")

    # Also create a simple list for re-transcription
    retranscribe_list = OUTPUT_DIR / "RETRANSCRIBE_LIST.txt"
    with open(retranscribe_list, "w", encoding="utf-8") as f:
        for i in issues:
            f.write(f"{i['chat']}/{i['file']}\n")
    print(f"File list saved to: {retranscribe_list}")


if __name__ == "__main__":
    main()
