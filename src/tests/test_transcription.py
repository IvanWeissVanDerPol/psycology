"""Test suite for transcription system.

Run with: pytest tests/ -v
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from transcription.utils.path_utils import (
    parse_date_from_filename,
    parse_filename,
    safe_filename,
)
from transcription.utils.quality import check_quality, is_quality_transcript
from transcription.config import PathConfig


class TestPathUtils:
    """Test path and filename parsing utilities."""

    def test_parse_date_from_filename_valid(self):
        """Test parsing valid WhatsApp filenames."""
        assert parse_date_from_filename("PTT-20240902-WA0017.opus") == "2024-09-02"
        assert parse_date_from_filename("AUD-20250720-WA0031.opus") == "2025-07-20"
        assert parse_date_from_filename("DOC-20241118-WA0011.pdf") == "2024-11-18"

    def test_parse_date_from_filename_invalid(self):
        """Test parsing invalid filenames."""
        assert parse_date_from_filename("invalid.txt") is None
        assert parse_date_from_filename("PTT-2024-WA0017.opus") is None
        assert parse_date_from_filename("") is None

    def test_parse_filename(self):
        """Test comprehensive filename parsing."""
        parsed = parse_filename("PTT-20240902-WA0017.opus")
        assert parsed.original == "PTT-20240902-WA0017.opus"
        assert parsed.date == "2024-09-02"
        assert parsed.file_type == "voice_note"
        assert parsed.message_id == "WA0017"

    def test_safe_filename(self):
        """Test filename sanitization."""
        assert safe_filename("file<name>.txt") == "file_name_.txt"
        assert safe_filename("file/name.txt") == "file_name.txt"
        assert safe_filename("normal.txt") == "normal.txt"


class TestQualityUtils:
    """Test quality checking utilities."""

    def test_check_quality_valid(self):
        """Test quality check on valid transcript."""
        text = "Hola, esto es una prueba de transcripción normal en español."
        result = check_quality(text)
        assert result.is_valid is True
        assert len(result.problems) == 0

    def test_check_quality_empty(self):
        """Test quality check on empty text."""
        result = check_quality("")
        assert result.is_valid is False
        assert "empty_text" in result.problems

    def test_check_quality_none(self):
        """Test quality check on None."""
        result = check_quality(None)
        assert result.is_valid is False
        assert "no_text" in result.problems

    def test_check_quality_too_short(self):
        """Test quality check on short text."""
        result = check_quality("hi")
        assert result.is_valid is False
        assert "too_short" in result.problems

    def test_check_quality_asian_chars(self):
        """Test detection of Asian characters (hallucination)."""
        text = "Hola esto es 日本語 text with many Asian characters 中文 日本語 한국어"
        result = check_quality(text)
        assert "asian_chars" in result.problems

    def test_check_quality_repetitive(self):
        """Test detection of repetitive text."""
        text = "hola hola hola hola hola hola"
        result = check_quality(text)
        assert result.is_valid is False

    def test_is_quality_transcript_quick_check(self):
        """Test quick quality check function."""
        assert is_quality_transcript("Hola esto es una prueba normal") is True
        assert is_quality_transcript("") is False
        assert is_quality_transcript(None) is False
        assert is_quality_transcript("hi") is False


class TestConfig:
    """Test configuration management."""

    def test_path_config_defaults(self):
        """Test path configuration defaults."""
        cfg = PathConfig()
        assert cfg.project_root.exists()
        assert isinstance(cfg.transcripts_source, Path)
        assert isinstance(cfg.transcripts_output, Path)


class TestIntegration:
    """Integration tests (require actual setup)."""

    @pytest.mark.skip(reason="Requires actual audio files")
    def test_transcribe_file(self):
        """Test full transcription flow."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
