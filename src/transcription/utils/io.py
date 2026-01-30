"""IO utilities for saving and loading transcript data.

Provides standardized methods for:
- JSON serialization
- Markdown generation
- Progress persistence
- Safe file operations
"""

from __future__ import annotations

import json
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from transcription.config import config
from transcription.utils.logging_utils import get_logger

logger = get_logger(__name__)


def save_json(data: Any, filepath: Path, indent: int = 2) -> bool:
    """Save data to JSON file atomically.

    Args:
        data: Data to serialize
        filepath: Target file path
        indent: JSON indentation level

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file first (atomic operation)
        temp_path = filepath.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent, default=str)

        # Atomic rename
        temp_path.replace(filepath)
        return True

    except (OSError, TypeError, ValueError) as e:
        logger.error(f"Failed to save JSON to {filepath}: {e}")
        return False


def load_json(filepath: Path, default: Optional[Any] = None) -> Any:
    """Load data from JSON file.

    Args:
        filepath: Source file path
        default: Default value if file doesn't exist or is invalid

    Returns:
        Loaded data or default value
    """
    if not filepath.exists():
        return default

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load JSON from {filepath}: {e}")
        return default


def load_transcripts(chat_name: str) -> list[dict]:
    """Load existing transcripts for a chat.

    Args:
        chat_name: Name of the chat

    Returns:
        List of transcript dictionaries
    """
    json_path = config.paths.transcripts_output / chat_name / "transcripts.json"
    data = load_json(json_path, [])

    if isinstance(data, list):
        return data
    return []


def save_transcripts(
    chat_name: str, transcripts: list[dict]
) -> tuple[Optional[Path], Optional[Path]]:
    """Save transcripts in both JSON and Markdown formats.

    Args:
        chat_name: Name of the chat
        transcripts: List of transcript dictionaries

    Returns:
        Tuple of (json_path, markdown_path) or (None, None) on failure
    """
    chat_output_dir = config.paths.transcripts_output / chat_name
    chat_output_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_path = chat_output_dir / "transcripts.json"
    if not save_json(transcripts, json_path):
        return None, None

    # Generate Markdown
    md_path = generate_markdown(chat_name, transcripts, chat_output_dir)

    return json_path, md_path


def generate_markdown(
    chat_name: str, transcripts: list[dict], output_dir: Path
) -> Optional[Path]:
    """Generate markdown report from transcripts.

    Args:
        chat_name: Name of the chat
        transcripts: List of transcript dictionaries
        output_dir: Directory to save markdown file

    Returns:
        Path to generated file or None on failure
    """
    try:
        # Group by date
        by_date = defaultdict(list)
        for t in transcripts:
            date = t.get("date") or "unknown"
            by_date[date].append(t)

        # Count successful transcriptions
        success_count = sum(1 for t in transcripts if t.get("success"))

        # Generate markdown content
        lines = [
            f"# Voice Note Transcripts: {chat_name}",
            "",
            f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"> Total files: {len(transcripts)}",
            f"> Successful: {success_count}",
            "",
            "---",
            "",
        ]

        for date in sorted(by_date.keys()):
            lines.append(f"## {date}")
            lines.append("")

            for t in sorted(by_date[date], key=lambda x: x["file"]):
                lines.append(f"### {t['file']}")
                lines.append("")

                if t.get("error"):
                    lines.append(f"**ERROR:** {t['error']}")
                    lines.append("")
                elif t.get("text"):
                    lines.append(t["text"])
                    lines.append("")
                    if t.get("duration"):
                        lines.append(f"*Duration: {t['duration']:.1f}s*")
                        lines.append("")
                else:
                    lines.append("*[Empty or inaudible]*")
                    lines.append("")

            lines.append("---")
            lines.append("")

        # Write markdown
        md_path = output_dir / "transcripts.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return md_path

    except OSError as e:
        logger.error(f"Failed to generate markdown for {chat_name}: {e}")
        return None


def save_progress_atomic(chat_name: str, results: dict[str, dict]) -> bool:
    """Save transcription progress atomically.

    Args:
        chat_name: Name of the chat
        results: Dictionary mapping filenames to transcript data

    Returns:
        True if successful
    """
    chat_output_dir = config.paths.transcripts_output / chat_name
    chat_output_dir.mkdir(parents=True, exist_ok=True)

    # Convert to list format
    transcripts = list(results.values())

    # Save both formats
    json_path, _ = save_transcripts(chat_name, transcripts)

    return json_path is not None


def get_already_transcribed(chat_name: str) -> set[str]:
    """Get set of filenames already successfully transcribed.

    Args:
        chat_name: Name of the chat

    Returns:
        Set of transcribed filenames
    """
    transcripts = load_transcripts(chat_name)
    return {t["file"] for t in transcripts if t.get("text") and not t.get("error")}
