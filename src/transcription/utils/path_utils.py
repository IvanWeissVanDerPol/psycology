"""Path utilities for the transcription system.

Provides standardized path handling, validation, and manipulation utilities.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ParsedFilename:
    """Parsed components from a WhatsApp filename."""

    original: str
    date: Optional[str] = None
    file_type: Optional[str] = None
    message_id: Optional[str] = None


def parse_date_from_filename(filename: str) -> Optional[str]:
    """Extract date from WhatsApp voice note filename.

    Supports formats:
        - PTT-20240902-WA0017.opus -> 2024-09-02
        - AUD-20250720-WA0031.opus -> 2025-07-20
        - DOC-20241118-WA0011.pdf -> 2024-11-18

    Args:
        filename: The filename to parse

    Returns:
        ISO format date string (YYYY-MM-DD) or None if parsing fails
    """
    try:
        # Extract the date portion (YYYYMMDD)
        parts = filename.split("-")
        if len(parts) >= 2:
            date_str = parts[1]
            if len(date_str) == 8 and date_str.isdigit():
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]

                # Validate date components
                if int(month) <= 12 and int(day) <= 31:
                    return f"{year}-{month}-{day}"
    except (ValueError, IndexError):
        pass

    return None


def parse_filename(filename: str) -> ParsedFilename:
    """Parse a WhatsApp filename into components.

    Args:
        filename: The filename to parse

    Returns:
        ParsedFilename with extracted components
    """
    # Determine file type from extension
    file_type = None
    if ".opus" in filename.lower():
        file_type = "voice_note"
    elif ".pdf" in filename.lower():
        file_type = "document"
    elif "." in filename:
        ext = filename.split(".")[-1].lower()
        if ext in ["webp", "jpg", "jpeg", "png"]:
            file_type = "image"

    # Extract message ID (WAxxxx)
    message_id = None
    wa_match = re.search(r"WA\d+", filename, re.IGNORECASE)
    if wa_match:
        message_id = wa_match.group()

    return ParsedFilename(
        original=filename,
        date=parse_date_from_filename(filename),
        file_type=file_type,
        message_id=message_id,
    )


def find_chat_directory(base_dir: Path, chat_name: str) -> Optional[Path]:
    """Find a chat directory by name (case-insensitive partial match).

    Args:
        base_dir: Base directory to search
        chat_name: Name or partial name of chat

    Returns:
        Path to chat directory or None if not found
    """
    if not base_dir.exists():
        return None

    chat_lower = chat_name.lower()

    for item in base_dir.iterdir():
        if item.is_dir() and chat_lower in item.name.lower():
            return item

    return None


def get_audio_files(
    directory: Path, extensions: Optional[set[str]] = None
) -> list[Path]:
    """Get all audio files in a directory.

    Args:
        directory: Directory to search
        extensions: Set of extensions to include (default: .opus)

    Returns:
        List of Path objects for audio files, sorted
    """
    if extensions is None:
        extensions = {".opus"}

    if not directory.exists():
        return []

    audio_files = []
    for ext in extensions:
        audio_files.extend(directory.glob(f"*{ext}"))

    return sorted(audio_files)


def ensure_directory(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        Path object (same as input)
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(filename: str) -> str:
    """Make a filename safe for filesystem use.

    Args:
        filename: Original filename

    Returns:
        Safe filename with special chars replaced
    """
    # Replace problematic characters
    safe = re.sub(r'[<>"/\\|?*]', "_", filename)
    # Remove control characters
    safe = "".join(char for char in safe if ord(char) >= 32)
    return safe.strip()
