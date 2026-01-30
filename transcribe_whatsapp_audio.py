#!/usr/bin/env python3
"""
WhatsApp Audio Transcription Script using OpenAI Whisper

This script transcribes all audio files in a WhatsApp chat directory
and saves the transcriptions in an organized format.

Requirements:
- pip install openai-whisper
- ffmpeg must be installed on the system

Usage:
    python transcribe_whatsapp_audio.py
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import argparse

try:
    import whisper
except ImportError:
    print("Error: whisper package not found. Please install it with:")
    print("pip install openai-whisper")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("transcription.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class WhatsAppAudioTranscriber:
    def __init__(
        self, source_dir: str, output_dir: str = None, model_name: str = "base"
    ):
        """
        Initialize the transcriber.

        Args:
            source_dir: Path to WhatsApp chat directory
            output_dir: Path to output directory for transcriptions
            model_name: Whisper model to use (tiny, base, small, medium, large)
        """
        self.source_dir = Path(source_dir)
        self.output_dir = (
            Path(output_dir) if output_dir else self.source_dir / "transcriptions"
        )
        self.model_name = model_name
        self.model = None

        # Create output directory
        self.output_dir.mkdir(exist_ok=True)

        # Supported audio formats
        self.audio_extensions = {".opus", ".mp3", ".wav", ".m4a", ".ogg", ".flac"}

        logger.info(f"Source directory: {self.source_dir}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Using Whisper model: {model_name}")

    def load_model(self):
        """Load the Whisper model."""
        try:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def find_audio_files(self) -> List[Path]:
        """
        Find all audio files in the source directory.

        Returns:
            List of Path objects for audio files
        """
        audio_files = []

        if not self.source_dir.exists():
            logger.error(f"Source directory does not exist: {self.source_dir}")
            return audio_files

        # Find all files with audio extensions
        for file_path in self.source_dir.rglob("*"):
            if (
                file_path.is_file()
                and file_path.suffix.lower() in self.audio_extensions
            ):
                audio_files.append(file_path)

        # Sort files by name for consistent processing
        audio_files.sort()

        logger.info(f"Found {len(audio_files)} audio files")
        return audio_files

    def transcribe_audio_file(self, audio_file: Path) -> Optional[Dict]:
        """
        Transcribe a single audio file.

        Args:
            audio_file: Path to the audio file

        Returns:
            Dictionary with transcription results or None if failed
        """
        try:
            logger.info(f"Transcribing: {audio_file.name}")

            # Transcribe the audio
            result = self.model.transcribe(
                str(audio_file),
                language=None,  # Auto-detect language
                task="transcribe",
                verbose=False,
            )

            # Create transcription result
            transcription = {
                "file_name": audio_file.name,
                "file_path": str(audio_file.relative_to(self.source_dir)),
                "file_size": audio_file.stat().st_size,
                "transcription_date": datetime.now().isoformat(),
                "duration": result.get("segments", [{}])[-1].get("end", 0)
                if result.get("segments")
                else 0,
                "detected_language": result.get("language", "unknown"),
                "text": result.get("text", "").strip(),
                "segments": result.get("segments", []),
            }

            logger.info(
                f"Transcribed {audio_file.name} ({transcription['duration']:.1f}s)"
            )
            return transcription

        except Exception as e:
            logger.error(f"Failed to transcribe {audio_file.name}: {e}")
            return None

    def save_transcription(self, transcription: Dict, format: str = "txt"):
        """
        Save transcription to file.

        Args:
            transcription: Transcription dictionary
            format: Output format ('txt', 'json', 'srt')
        """
        base_name = Path(transcription["file_name"]).stem

        if format == "txt":
            # Save as plain text
            output_file = self.output_dir / f"{base_name}.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"File: {transcription['file_name']}\n")
                f.write(f"Date: {transcription['transcription_date']}\n")
                f.write(f"Duration: {transcription['duration']:.1f}s\n")
                f.write(f"Language: {transcription['detected_language']}\n")
                f.write(f"Size: {transcription['file_size']:,} bytes\n")
                f.write("-" * 50 + "\n\n")
                f.write(transcription["text"])

        elif format == "json":
            # Save as JSON
            output_file = self.output_dir / f"{base_name}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(transcription, f, indent=2, ensure_ascii=False)

        elif format == "srt":
            # Save as SRT subtitles
            output_file = self.output_dir / f"{base_name}.srt"
            with open(output_file, "w", encoding="utf-8") as f:
                for i, segment in enumerate(transcription["segments"], 1):
                    start_time = self._format_srt_time(segment["start"])
                    end_time = self._format_srt_time(segment["end"])
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment['text'].strip()}\n\n")

        logger.info(f"Saved {format.upper()} file: {output_file}")

    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds as SRT timestamp."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def create_summary_report(self, transcriptions: List[Dict]):
        """
        Create a summary report of all transcriptions.

        Args:
            transcriptions: List of transcription dictionaries
        """
        report_file = self.output_dir / "transcription_summary.md"

        total_files = len(transcriptions)
        total_duration = sum(t["duration"] for t in transcriptions)
        total_size = sum(t["file_size"] for t in transcriptions)

        # Language statistics
        languages = {}
        for t in transcriptions:
            lang = t["detected_language"]
            languages[lang] = languages.get(lang, 0) + 1

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# WhatsApp Audio Transcription Summary\n\n")
            f.write(
                f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            f.write("## Statistics\n\n")
            f.write(f"- **Total Files:** {total_files}\n")
            f.write(f"- **Total Duration:** {total_duration / 60:.1f} minutes\n")
            f.write(f"- **Total Size:** {total_size / 1024 / 1024:.1f} MB\n")
            f.write(
                f"- **Average Duration:** {total_duration / total_files:.1f} seconds\n\n"
            )

            f.write("## Languages Detected\n\n")
            for lang, count in sorted(languages.items()):
                f.write(f"- **{lang}:** {count} files\n")
            f.write("\n")

            f.write("## Files Transcribed\n\n")
            f.write("| Filename | Duration | Language | Size |\n")
            f.write("|----------|----------|----------|------|\n")

            for t in sorted(transcriptions, key=lambda x: x["file_name"]):
                f.write(
                    f"| {t['file_name']} | {t['duration']:.1f}s | {t['detected_language']} | {t['file_size']:,} bytes |\n"
                )

        logger.info(f"Created summary report: {report_file}")

    def transcribe_all(
        self, formats: List[str] = ["txt", "json"], skip_existing: bool = True
    ):
        """
        Transcribe all audio files in the directory.

        Args:
            formats: List of output formats to generate
            skip_existing: Whether to skip files that already have transcriptions
        """
        # Load the model
        self.load_model()

        # Find all audio files
        audio_files = self.find_audio_files()

        if not audio_files:
            logger.warning("No audio files found")
            return

        transcriptions = []

        # Process each audio file
        for audio_file in audio_files:
            # Check if transcription already exists
            if skip_existing:
                base_name = audio_file.stem
                existing_files = [
                    self.output_dir / f"{base_name}.{fmt}" for fmt in formats
                ]
                if any(f.exists() for f in existing_files):
                    logger.info(f"Skipping {audio_file.name} (already transcribed)")
                    continue

            # Transcribe the file
            transcription = self.transcribe_audio_file(audio_file)

            if transcription:
                transcriptions.append(transcription)

                # Save in requested formats
                for format in formats:
                    self.save_transcription(transcription, format)

        # Create summary report
        if transcriptions:
            self.create_summary_report(transcriptions)
            logger.info(f"Successfully transcribed {len(transcriptions)} files")
        else:
            logger.info("No new files were transcribed")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Transcribe WhatsApp audio files using Whisper"
    )
    parser.add_argument("source_dir", help="Path to WhatsApp chat directory")
    parser.add_argument("--output-dir", help="Output directory for transcriptions")
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model to use (default: base)",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        default=["txt", "json"],
        choices=["txt", "json", "srt"],
        help="Output formats to generate (default: txt json)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing transcriptions"
    )

    args = parser.parse_args()

    # Validate source directory
    if not Path(args.source_dir).exists():
        print(f"Error: Source directory does not exist: {args.source_dir}")
        sys.exit(1)

    # Create transcriber and run
    transcriber = WhatsAppAudioTranscriber(
        source_dir=args.source_dir, output_dir=args.output_dir, model_name=args.model
    )

    try:
        transcriber.transcribe_all(formats=args.formats, skip_existing=not args.force)
        print("\nTranscription completed successfully!")
        print(f"Check the output directory: {transcriber.output_dir}")

    except KeyboardInterrupt:
        print("\nTranscription interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during transcription: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
