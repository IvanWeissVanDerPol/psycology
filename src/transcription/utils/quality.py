"""Quality checking utilities for transcript validation.

Provides comprehensive quality checks for transcribed text to identify:
- Hallucinations (Asian characters in Spanish audio)
- Repetitive patterns
- Gibberish detection
- Language mixing issues
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from transcription.config import config


@dataclass
class QualityResult:
    """Result of quality check on a transcript."""

    is_valid: bool = True
    problems: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def add_problem(self, problem: str, detail: Optional[str] = None) -> None:
        """Add a problem to the result."""
        self.is_valid = False
        self.problems.append(problem)
        if detail:
            self.details[problem] = detail


def check_quality(text: Optional[str]) -> QualityResult:
    """Check transcript quality and return detailed result.

    Args:
        text: Transcribed text to check

    Returns:
        QualityResult with validation status and problem details
    """
    result = QualityResult()

    if text is None:
        result.add_problem("no_text", "Text is None")
        return result

    text = text.strip()
    if not text:
        result.add_problem("empty_text", "Text is empty after stripping")
        return result

    words = text.split()
    word_count = len(words)

    # Check minimum word count
    if word_count < config.quality.min_words:
        result.add_problem(
            "too_short", f"Only {word_count} words (min: {config.quality.min_words})"
        )
        return result

    # Check for Asian characters (Whisper hallucination in Spanish audio)
    asian_chars = len(
        re.findall(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]", text)
    )
    if asian_chars > config.quality.max_asian_chars:
        result.add_problem(
            "asian_chars",
            f"Found {asian_chars} Asian characters (max: {config.quality.max_asian_chars})",
        )

    # Check for excessive repetition
    if re.search(r"(.{15,})\1{2,}", text):
        result.add_problem("repetitive_phrase", "Same phrase repeated 3+ times")

    # Check for word repetition
    if re.search(r"\b(\w+)\s+\1\s+\1\s+\1\b", text.lower()):
        result.add_problem("word_repetition", "Same word 4+ times in a row")

    # Check for punctuation spam
    if re.search(r"\.{5,}|\?{4,}|!{4,}", text):
        result.add_problem("punct_spam", "Excessive punctuation")

    # Check for high English mix in Spanish audio
    english_words = len(
        re.findall(
            r"\b(the|and|but|with|for|this|that|what|have|from|are|was|were|been|will|would|could|should)\b",
            text.lower(),
        )
    )
    if english_words > config.quality.max_english_words:
        result.add_problem(
            "english_mix",
            f"{english_words} English words found (max: {config.quality.max_english_words})",
        )

    # Check for gibberish (unusual consonant clusters)
    gibberish = len(re.findall(r"[bcdfghjklmnpqrstvwxyz]{5,}", text.lower()))
    if gibberish > config.quality.max_gibberish_clusters:
        result.add_problem("gibberish", f"{gibberish} unusual consonant clusters")

    # Check for low vocabulary diversity (repetitive content)
    unique_words = set(w.lower() for w in words)
    if len(words) > 10:  # Only check for longer texts
        unique_ratio = len(unique_words) / len(words)
        if unique_ratio < config.quality.min_unique_word_ratio:
            result.add_problem(
                "low_diversity",
                f"Vocabulary diversity: {unique_ratio:.2%} (min: {config.quality.min_unique_word_ratio:.0%})",
            )

    return result


def is_quality_transcript(text: Optional[str], min_words: Optional[int] = None) -> bool:
    """Quick check if transcript meets quality standards.

    Args:
        text: Transcribed text to check
        min_words: Optional override for minimum word count

    Returns:
        True if transcript is good quality, False otherwise
    """
    if text is None:
        return False

    text = text.strip()
    if len(text) < 30:
        return False

    words = text.split()
    min_word_count = min_words or config.quality.min_words
    if len(words) < min_word_count:
        return False

    # Quick checks for obvious problems
    # Asian characters
    if (
        len(re.findall(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]", text))
        > 5
    ):
        return False

    # Vocabulary diversity
    unique_words = set(w.lower() for w in words)
    if (
        len(words) > 10
        and len(unique_words) / len(words) < config.quality.min_unique_word_ratio
    ):
        return False

    return True


def format_quality_report(result: QualityResult) -> str:
    """Format quality result as human-readable string.

    Args:
        result: QualityResult to format

    Returns:
        Formatted report string
    """
    if result.is_valid:
        return "✓ Quality check passed"

    lines = ["✗ Quality issues found:"]
    for problem in result.problems:
        detail = result.details.get(problem, "")
        if detail:
            lines.append(f"  - {problem}: {detail}")
        else:
            lines.append(f"  - {problem}")

    return "\n".join(lines)
