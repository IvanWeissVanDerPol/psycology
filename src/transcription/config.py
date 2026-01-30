"""Centralized configuration management for transcription system.

This module provides a unified configuration interface that loads settings from:
1. Environment variables (highest priority)
2. Configuration files (config/ directory)
3. Default values (lowest priority)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Base paths - relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


@dataclass(frozen=True)
class PathConfig:
    """Directory and file path configuration."""

    project_root: Path = field(default_factory=lambda: PROJECT_ROOT)
    transcripts_source: Path = field(
        default_factory=lambda: PROJECT_ROOT
        / "SOURCE_OF_TRUTH"
        / "whatsapp transcripts"
    )
    transcripts_output: Path = field(
        default_factory=lambda: PROJECT_ROOT
        / "SOURCE_OF_TRUTH"
        / "voice_note_transcripts"
    )
    source_of_truth: Path = field(
        default_factory=lambda: PROJECT_ROOT / "SOURCE_OF_TRUTH"
    )

    def __post_init__(self) -> None:
        """Ensure all paths are Path objects."""
        # Convert string paths to Path objects if needed
        for attr_name in [
            "project_root",
            "transcripts_source",
            "transcripts_output",
            "source_of_truth",
        ]:
            value = getattr(self, attr_name)
            if isinstance(value, str):
                object.__setattr__(self, attr_name, Path(value))


@dataclass(frozen=True)
class ModelConfig:
    """Whisper model configuration."""

    default_model: str = field(
        default_factory=lambda: os.getenv("TRANSCRIPTION_MODEL", "base")
    )
    default_language: str = field(
        default_factory=lambda: os.getenv("TRANSCRIPTION_LANGUAGE", "es")
    )
    use_fp16: bool = field(
        default_factory=lambda: os.getenv("USE_GPU", "false").lower() == "true"
    )
    max_workers: int = field(
        default_factory=lambda: int(os.getenv("TRANSCRIPTION_WORKERS", "4"))
    )


@dataclass(frozen=True)
class ProcessingConfig:
    """Processing and performance settings."""

    batch_size: int = field(default_factory=lambda: int(os.getenv("BATCH_SIZE", "50")))
    save_interval: int = field(
        default_factory=lambda: int(os.getenv("SAVE_INTERVAL", "10"))
    )
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("TIMEOUT_SECONDS", "300"))
    )


@dataclass(frozen=True)
class QualityConfig:
    """Quality control thresholds."""

    min_words: int = field(default_factory=lambda: int(os.getenv("MIN_WORDS", "3")))
    max_asian_chars: int = field(
        default_factory=lambda: int(os.getenv("MAX_ASIAN_CHARS", "3"))
    )
    min_unique_word_ratio: float = field(
        default_factory=lambda: float(os.getenv("MIN_UNIQUE_WORD_RATIO", "0.25"))
    )
    max_gibberish_clusters: int = field(
        default_factory=lambda: int(os.getenv("MAX_GIBBERISH_CLUSTERS", "3"))
    )
    max_english_words: int = field(
        default_factory=lambda: int(os.getenv("MAX_ENGLISH_WORDS", "8"))
    )


@dataclass(frozen=True)
class FFmpegConfig:
    """FFmpeg configuration."""

    paths: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Load paths from environment or use defaults."""
        if not self.paths:
            # Try environment variable first
            env_path = os.getenv("FFMPEG_PATH", "")
            if env_path:
                paths = [env_path]
            else:
                # Default common paths
                paths = [
                    r"C:\ffmpeg\bin",
                    r"C:\Program Files\ffmpeg\bin",
                    r"C:\Users\Alejandro\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin",
                    "/usr/bin",  # Linux/Mac
                    "/usr/local/bin",
                ]
            object.__setattr__(self, "paths", paths)

    def find_ffmpeg(self) -> Optional[Path]:
        """Find ffmpeg executable in configured paths."""
        for path_str in self.paths:
            path = Path(path_str)
            if path.exists():
                ffmpeg_exe = path / "ffmpeg.exe" if os.name == "nt" else path / "ffmpeg"
                if ffmpeg_exe.exists():
                    return path
        return None


@dataclass(frozen=True)
class LoggingConfig:
    """Logging configuration."""

    level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    format_string: str = field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_logging: bool = field(
        default_factory=lambda: os.getenv("FILE_LOGGING", "true").lower() == "true"
    )
    log_file: Path = field(
        default_factory=lambda: PROJECT_ROOT / "logs" / "transcription.log"
    )

    def __post_init__(self) -> None:
        """Ensure log directory exists."""
        log_dir = Path(self.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)


class Config:
    """Main configuration class - singleton pattern."""

    _instance: Optional[Config] = None

    def __new__(cls) -> Config:
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize configuration if not already done."""
        if self._initialized:
            return

        self.paths = PathConfig()
        self.model = ModelConfig()
        self.processing = ProcessingConfig()
        self.quality = QualityConfig()
        self.ffmpeg = FFmpegConfig()
        self.logging = LoggingConfig()

        self._initialized = True
        self._setup_ffmpeg_path()

    def _setup_ffmpeg_path(self) -> None:
        """Add ffmpeg to system PATH if found."""
        ffmpeg_path = self.ffmpeg.find_ffmpeg()
        if ffmpeg_path:
            current_path = os.environ.get("PATH", "")
            if str(ffmpeg_path) not in current_path:
                os.environ["PATH"] = str(ffmpeg_path) + os.pathsep + current_path
                logging.debug(f"Added ffmpeg to PATH: {ffmpeg_path}")

    def validate(self) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Check critical paths
        if not self.paths.transcripts_source.exists():
            issues.append(
                f"Transcripts source directory does not exist: {self.paths.transcripts_source}"
            )

        # Check model name
        valid_models = ["tiny", "base", "small", "medium", "large", "turbo"]
        if self.model.default_model not in valid_models:
            issues.append(
                f"Invalid model: {self.model.default_model}. Must be one of: {valid_models}"
            )

        # Check ffmpeg
        if not self.ffmpeg.find_ffmpeg():
            issues.append("FFmpeg not found in any configured path")

        return issues


# Global config instance
config = Config()
