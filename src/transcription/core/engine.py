"""Transcription engine using Whisper.

Provides a unified interface for audio transcription with:
- Model caching
- Error handling
- Progress tracking
- Quality validation
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, TYPE_CHECKING

from transcription.config import config
from transcription.utils.logging_utils import get_logger
from transcription.utils.path_utils import parse_date_from_filename
from transcription.utils.quality import check_quality

if TYPE_CHECKING:
    import whisper

logger = get_logger(__name__)

# Module-level model cache
_model_cache: dict[str, "whisper.Whisper"] = {}


def get_model(model_name: str) -> "whisper.Whisper":
    """Get or load a Whisper model (cached).

    Args:
        model_name: Model size name (tiny, base, small, medium, large, turbo)

    Returns:
        Loaded Whisper model

    Raises:
        ImportError: If whisper module is not installed
        RuntimeError: If model fails to load
    """
    global _model_cache

    if model_name in _model_cache:
        return _model_cache[model_name]

    try:
        import whisper
    except ImportError as e:
        raise ImportError(
            "whisper module not found. Install with: pip install openai-whisper"
        ) from e

    try:
        logger.info(f"Loading Whisper model: {model_name}")
        model = whisper.load_model(model_name)
        _model_cache[model_name] = model
        logger.info(f"Model '{model_name}' loaded successfully")
        return model
    except Exception as e:
        raise RuntimeError(f"Failed to load Whisper model '{model_name}': {e}") from e


def clear_model_cache() -> None:
    """Clear the model cache to free memory."""
    global _model_cache
    _model_cache.clear()
    logger.debug("Model cache cleared")


def transcribe_file(
    file_path: Path,
    model_name: Optional[str] = None,
    language: Optional[str] = None,
    validate_quality: bool = True,
) -> dict:
    """Transcribe a single audio file.

    Args:
        file_path: Path to audio file
        model_name: Whisper model to use (default from config)
        language: Language code (default from config)
        validate_quality: Whether to run quality checks

    Returns:
        Dictionary with transcription results
    """
    model_name = model_name or config.model.default_model
    language = language or config.model.default_language

    result = {
        "file": file_path.name,
        "date": parse_date_from_filename(file_path.name),
        "text": None,
        "language": language,
        "duration": None,
        "success": False,
        "model": model_name,
        "quality_issues": [],
    }

    try:
        model = get_model(model_name)

        # Perform transcription
        transcription = model.transcribe(
            str(file_path),
            language=language,
            fp16=config.model.use_fp16,
            verbose=False,
        )

        # Extract text safely
        text = transcription.get("text", "")
        if isinstance(text, list):
            text = " ".join(text)
        text = str(text).strip() if text else ""

        result["text"] = text
        result["duration"] = transcription.get("duration")
        result["language"] = transcription.get("language", language)
        result["success"] = True

        # Quality validation
        if validate_quality and text:
            quality_result = check_quality(text)
            if not quality_result.is_valid:
                result["quality_issues"] = quality_result.problems
                logger.warning(
                    f"Quality issues in {file_path.name}: {quality_result.problems}"
                )

        logger.debug(f"Transcribed {file_path.name}: {len(text)} chars")

    except Exception as e:
        result["error"] = str(e)
        result["success"] = False
        logger.error(f"Failed to transcribe {file_path.name}: {e}")

    return result


def transcribe_with_segments(
    file_path: Path,
    model_name: Optional[str] = None,
    language: Optional[str] = None,
) -> dict:
    """Transcribe with full segment information (for detailed analysis).

    Args:
        file_path: Path to audio file
        model_name: Whisper model to use
        language: Language code

    Returns:
        Dictionary with transcription results including segments
    """
    model_name = model_name or config.model.default_model
    language = language or config.model.default_language

    result = {
        "file": file_path.name,
        "date": parse_date_from_filename(file_path.name),
        "text": None,
        "language": language,
        "duration": None,
        "segments": [],
        "success": False,
        "model": model_name,
    }

    try:
        model = get_model(model_name)

        transcription = model.transcribe(
            str(file_path),
            language=language,
            fp16=config.model.use_fp16,
            verbose=False,
        )

        # Extract text
        text = transcription.get("text", "")
        if isinstance(text, list):
            text = " ".join(text)
        text = str(text).strip() if text else ""

        # Extract segments
        segments = transcription.get("segments", [])
        formatted_segments = []
        for seg in segments:
            if isinstance(seg, dict):
                formatted_segments.append(
                    {
                        "start": seg.get("start"),
                        "end": seg.get("end"),
                        "text": str(seg.get("text", "")).strip(),
                    }
                )

        result["text"] = text
        result["duration"] = transcription.get("duration")
        result["language"] = transcription.get("language", language)
        result["segments"] = formatted_segments
        result["success"] = True

    except Exception as e:
        result["error"] = str(e)
        result["success"] = False
        logger.error(f"Failed to transcribe {file_path.name}: {e}")

    return result
