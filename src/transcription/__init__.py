"""Transcription module - Unified voice note transcription system.

This module provides a complete transcription pipeline with:
- Configuration management
- Quality validation
- Multiple processing modes
- Progress persistence
"""

from transcription.config import Config, config
from transcription.core.engine import get_model, transcribe_file, clear_model_cache
from transcription.utils.io import (
    save_json,
    load_json,
    load_transcripts,
    save_transcripts,
    get_already_transcribed,
)
from transcription.utils.path_utils import (
    parse_date_from_filename,
    parse_filename,
    find_chat_directory,
    get_audio_files,
)
from transcription.utils.quality import check_quality, is_quality_transcript
from transcription.utils.logging_utils import setup_logging, get_logger

__version__ = "2.0.0"

__all__ = [
    "Config",
    "config",
    "get_model",
    "transcribe_file",
    "clear_model_cache",
    "save_json",
    "load_json",
    "load_transcripts",
    "save_transcripts",
    "get_already_transcribed",
    "parse_date_from_filename",
    "parse_filename",
    "find_chat_directory",
    "get_audio_files",
    "check_quality",
    "is_quality_transcript",
    "setup_logging",
    "get_logger",
]
