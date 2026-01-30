#!/usr/bin/env python3
"""
Deep Psychological Extraction from Voice Note Transcripts

Refactored version with:
- Pattern configuration from JSON file
- Integration with transcription module utilities
- Proper error handling and logging
- Type hints throughout
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from transcription import config
from transcription.utils.logging_utils import setup_logging
from transcription.utils.quality import is_quality_transcript

logger = setup_logging(__name__)


@dataclass
class PatternCategory:
    """A category of psychological patterns."""

    name: str
    description: str
    priority: str
    patterns: list[str] = field(default_factory=list)


@dataclass
class PatternMatch:
    """A single pattern match with context."""

    pattern: str
    matched_text: str
    context: str
    file: str
    date: Optional[str] = None


@dataclass
class ExtractionResult:
    """Results of extracting patterns from transcripts."""

    chat_name: str
    total_files: int
    quality_files: int
    findings: dict[str, list[PatternMatch]] = field(default_factory=dict)
    date_range: Optional[tuple[str, str]] = None


class PatternConfig:
    """Load and manage psychological pattern configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize pattern configuration.

        Args:
            config_path: Path to JSON config file (default: config/psychological_patterns.json)
        """
        if config_path is None:
            config_path = (
                config.paths.project_root / "config" / "psychological_patterns.json"
            )

        self.config_path = config_path
        self.categories: dict[str, PatternCategory] = {}
        self.high_value_categories: list[str] = []
        self.settings: dict = {}

        self._load_config()

    def _load_config(self) -> None:
        """Load pattern configuration from JSON file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Parse categories
            for name, cat_data in data.get("categories", {}).items():
                self.categories[name] = PatternCategory(
                    name=name,
                    description=cat_data.get("description", ""),
                    priority=cat_data.get("priority", "medium"),
                    patterns=cat_data.get("patterns", []),
                )

            self.high_value_categories = data.get("high_value_categories", [])
            self.settings = data.get("settings", {})

            logger.info(
                f"Loaded {len(self.categories)} pattern categories from {self.config_path}"
            )

        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load pattern config from {self.config_path}: {e}")
            raise RuntimeError(f"Cannot load pattern configuration: {e}") from e

    def get_category(self, name: str) -> Optional[PatternCategory]:
        """Get a category by name."""
        return self.categories.get(name)

    def get_patterns_for_category(self, name: str) -> list[str]:
        """Get regex patterns for a category."""
        cat = self.categories.get(name)
        return cat.patterns if cat else []


class PsychologicalExtractor:
    """Extract psychological patterns from transcript text."""

    def __init__(self, pattern_config: Optional[PatternConfig] = None):
        """Initialize extractor with pattern configuration.

        Args:
            pattern_config: Pattern configuration (default: load from file)
        """
        self.pattern_config = pattern_config or PatternConfig()
        self.context_chars = self.pattern_config.settings.get("context_chars", 150)

    def extract_context(self, text: str, match_start: int, match_end: int) -> str:
        """Extract context around a regex match.

        Args:
            text: Full text
            match_start: Start position of match
            match_end: End position of match

        Returns:
            Context string with ellipsis if truncated
        """
        start = max(0, match_start - self.context_chars)
        end = min(len(text), match_end + self.context_chars)

        context = text[start:end]
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."

        return context.strip()

    def analyze_text(self, text: str) -> dict[str, list[dict]]:
        """Analyze text for all psychological patterns.

        Args:
            text: Text to analyze

        Returns:
            Dictionary mapping category names to list of matches
        """
        results: dict[str, list[dict]] = defaultdict(list)
        text_lower = text.lower()

        for category_name, category in self.pattern_config.categories.items():
            for pattern in category.patterns:
                try:
                    for match in re.finditer(pattern, text_lower):
                        context = self.extract_context(text, match.start(), match.end())
                        results[category_name].append(
                            {
                                "pattern": pattern,
                                "matched_text": match.group(),
                                "context": context,
                            }
                        )
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")

        return dict(results)

    def process_transcripts(
        self, chat_name: str, transcripts: list[dict]
    ) -> ExtractionResult:
        """Process all transcripts for a chat.

        Args:
            chat_name: Name of the chat
            transcripts: List of transcript dictionaries

        Returns:
            ExtractionResult with findings
        """
        result = ExtractionResult(
            chat_name=chat_name,
            total_files=len(transcripts),
            quality_files=0,
            findings=defaultdict(list),
        )

        dates: list[str] = []
        min_words = self.pattern_config.settings.get("quality_min_words", 10)

        for t in transcripts:
            text = t.get("text", "")
            if not is_quality_transcript(text, min_words=min_words):
                continue

            result.quality_files += 1

            if t.get("date"):
                dates.append(t["date"])

            analysis = self.analyze_text(text)

            for category, matches in analysis.items():
                for match in matches:
                    result.findings[category].append(
                        PatternMatch(
                            pattern=match["pattern"],
                            matched_text=match["matched_text"],
                            context=match["context"],
                            file=t["file"],
                            date=t.get("date"),
                        )
                    )

        if dates:
            result.date_range = (min(dates), max(dates))

        return result


def generate_markdown_report(results: dict[str, ExtractionResult]) -> str:
    """Generate comprehensive markdown report from extraction results.

    Args:
        results: Dictionary mapping chat names to ExtractionResult

    Returns:
        Markdown formatted report
    """
    lines = [
        "# Comprehensive Voice Note Psychological Extraction",
        "",
        f"> **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "> **Method:** Deep pattern extraction across all transcripts",
        "",
        "---",
        "",
        "## Summary Statistics",
        "",
        "| Chat | Total Files | Quality Files | Key Categories |",
        "|------|-------------|---------------|----------------|",
    ]

    for chat_name, result in sorted(results.items()):
        # Get top 3 categories by finding count
        sorted_cats = sorted(
            result.findings.items(), key=lambda x: len(x[1]), reverse=True
        )
        key_cats = [cat for cat, findings in sorted_cats if len(findings) >= 3][:3]
        key_cats_str = ", ".join(key_cats) if key_cats else "none"

        lines.append(
            f"| {chat_name} | {result.total_files} | {result.quality_files} | {key_cats_str} |"
        )

    lines.extend(["", "---", ""])

    # Per-chat detailed findings
    for chat_name, result in sorted(results.items()):
        lines.append(f"## {chat_name}")
        lines.append("")

        if result.date_range:
            lines.append(
                f"**Date Range:** {result.date_range[0]} to {result.date_range[1]}"
            )
            lines.append("")

        if not result.findings:
            lines.append("*No significant findings in quality transcripts.*")
            lines.append("")
            continue

        # Group by category
        min_findings = 2  # Configurable
        max_examples = 5  # Configurable

        for category in sorted(result.findings.keys()):
            findings = result.findings[category]
            if len(findings) < min_findings:
                continue

            lines.append(
                f"### {category.replace('_', ' ').title()} ({len(findings)} occurrences)"
            )
            lines.append("")

            # Show top examples
            for finding in findings[:max_examples]:
                lines.append(f"**{finding.file}** ({finding.date or 'unknown'})")
                lines.append(f"> {finding.context}")
                lines.append("")

            if len(findings) > max_examples:
                lines.append(
                    f"*... and {len(findings) - max_examples} more occurrences*"
                )
                lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def save_category_export(
    results: dict[str, ExtractionResult],
    high_value_categories: list[str],
    output_path: Path,
) -> None:
    """Save category-specific findings to JSON.

    Args:
        results: Extraction results by chat
        high_value_categories: Categories to export
        output_path: Path to save JSON file
    """
    category_export: dict[str, list[dict]] = {}

    for chat_name, result in results.items():
        for category in high_value_categories:
            if category not in result.findings:
                continue

            if category not in category_export:
                category_export[category] = []

            for match in result.findings[category]:
                category_export[category].append(
                    {
                        "chat": chat_name,
                        "file": match.file,
                        "date": match.date,
                        "context": match.context,
                        "pattern": match.pattern,
                    }
                )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(category_export, f, indent=2, ensure_ascii=False)

    logger.info(f"Category export saved to: {output_path}")


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    logger.info("=" * 60)
    logger.info("DEEP PSYCHOLOGICAL EXTRACTION FROM VOICE NOTES")
    logger.info("=" * 60)

    try:
        # Load pattern configuration
        pattern_config = PatternConfig()
        extractor = PsychologicalExtractor(pattern_config)

        # Process all chats
        all_results: dict[str, ExtractionResult] = {}

        if not config.paths.transcripts_output.exists():
            logger.error(
                f"Transcripts directory not found: {config.paths.transcripts_output}"
            )
            return 1

        for chat_dir in sorted(config.paths.transcripts_output.iterdir()):
            if not chat_dir.is_dir():
                continue

            chat_name = chat_dir.name
            json_path = chat_dir / "transcripts.json"

            if not json_path.exists():
                continue

            # Load transcripts
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    transcripts = json.load(f)
                    valid = [
                        t for t in transcripts if t.get("text") and not t.get("error")
                    ]
            except (OSError, json.JSONDecodeError) as e:
                logger.error(f"Failed to load {chat_name}: {e}")
                continue

            if not valid:
                continue

            logger.info(f"Processing {chat_name} ({len(valid)} transcripts)...")

            # Extract patterns
            result = extractor.process_transcripts(chat_name, valid)
            all_results[chat_name] = result

            # Print summary
            total_findings = sum(len(f) for f in result.findings.values())
            logger.info(
                f"  -> {result.quality_files} quality transcripts, {total_findings} findings"
            )

        # Generate report
        logger.info("Generating comprehensive report...")
        report = generate_markdown_report(all_results)

        output_path = config.paths.source_of_truth / "DEEP_EXTRACTION_REPORT.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"Report saved to: {output_path}")

        # Generate category export
        logger.info("Generating category exports...")
        cat_path = config.paths.source_of_truth / "CATEGORY_EXTRACTION.json"
        save_category_export(
            all_results, pattern_config.high_value_categories, cat_path
        )

        # Print summary
        logger.info("=" * 60)
        logger.info("HIGH-VALUE CATEGORY SUMMARY")
        logger.info("=" * 60)

        # Load the export we just saved to get counts
        with open(cat_path, "r", encoding="utf-8") as f:
            category_export = json.load(f)

        for cat in pattern_config.high_value_categories:
            count = len(category_export.get(cat, []))
            if count > 0:
                logger.info(f"  {cat}: {count} findings")

        logger.info("Done!")
        return 0

    except Exception as e:
        logger.exception(f"Extraction failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
