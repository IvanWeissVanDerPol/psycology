#!/usr/bin/env python3
"""
Quick Analysis of Defi Voice Recordings for Psychological Insights

Usage: python analyze_defi_audio.py /path/to/whatsapp/transcripts/Defi/
"""

import os
import subprocess
import json
from pathlib import Path


def get_transcription_file(opus_file):
    """Extract text from .opus file using whisper."""
    try:
        result = subprocess.run(
            ["whisper", "-m", "tiny", "-l", "es", "--output-format", "json", opus_file],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            output = json.loads(result.stdout)
            return output.get("text", "")
    except Exception as e:
        return f"Error processing {opus_file}: {e}"


def analyze_defi_relationship(audio_files):
    """Analyze patterns in Defi audio recordings."""

    insights = {
        "audio_count": len(audio_files),
        "patterns": {
            "defi_responses": [],
            "emotional_vulnerability": [],
            "care_dynamics": [],
            "friendship_support": [],
            "breakup_processing": [],
        },
        "key_themes": [],
        "recommendations": [],
    }

    print(f"Analyzing {len(audio_files)} Defi audio files...")

    for i, audio_file in enumerate(audio_files[:10]):  # Sample first 10
        transcription = get_transcription_file(audio_file)
        if not transcription:
            print(f"Could not process {audio_file}")
            continue

        text = transcription.lower()
        file_name = os.path.basename(audio_file)

        # Look for Defi's responses
        if any(
            keyword in text
            for keyword in ["te ayudo", "gracias", "perfecto", "buenisimo", "excelente"]
        ):
            insights["patterns"]["defi_responses"].append(f"  {file_name} - {keyword}")

        # Look for emotional vulnerability
        if any(
            keyword in text
            for keyword in ["no pued", "me cago", "estoy mal", "mal", "pobre"]
        ):
            insights["patterns"]["emotional_vulnerability"].append(
                f"  {file_name} - emotional disclosure"
            )

        # Look for care dynamics
        if any(
            keyword in text
            for keyword in [
                "ayudar",
                "cuidar",
                "apoyar",
                "estar presente",
                "aquí estoy",
            ]
        ):
            insights["patterns"]["care_dynamics"].append(
                f"  {file_name} - care offering/receiving"
            )

        # Look for Ivan asking for help
        if any(
            keyword in text
            for keyword in ["necesito", "por favor", "ayuda", "ayudame", "ayúdame"]
        ):
            insights["patterns"]["care_dynamics"].append(
                f"  {file_name} - Ivan needs help"
            )

        # Look for friendship support
        if any(
            keyword in text
            for keyword in ["amigos", "cariño", "fuerza", "confío", "te quiero"]
        ):
            insights["patterns"]["friendship_support"].append(
                f"  {file_name} - friendship expression"
            )

        # Check if this is about Laura breakup
        if any(
            keyword in text
            for keyword in ["laura", "terminó", "rompimos", "relación", "sola"]
        ):
            insights["patterns"]["breakup_processing"].append(
                f"  {file_name} - Laura breakup"
            )

        # Look for The Fixer patterns
        if any(
            keyword in text
            for keyword in [
                "resuelvo",
                "cocino",
                "masaje",
                "ayudo con",
                "programo",
                "sistema",
                "busco",
            ]
        ):
            insights["patterns"]["care_dynamics"].append(
                f"  {file_name} - The Fixer active"
            )

    return insights


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyze_defi_audio.py /path/to/whatsapp/transcripts/Defi/")
        return

    audio_path = Path(sys.argv[1])

    if not audio_path.exists():
        print(f"Path not found: {audio_path}")
        return

    # Get all audio files
    audio_files = list(audio_path.glob("*.opus"))

    results = analyze_defi_relationship(audio_files)

    print("\n" + "=" * 50)
    print(f"ANALYSIS RESULTS FOR {audio_path.name}")
    print("=" * 50)

    print(f"Audio files processed: {results['audio_count']}")
    print("\nPATTERNS FOUND:")

    for pattern, examples in results["patterns"].items():
        if examples:
            print(f"  {pattern}:")
            for example in examples[:3]:  # Show first 3
                print(f"    - {example}")
        print()

    print("\nKEY INSIGHTS:")
    for theme in results["key_themes"]:
        if results["key_themes"][theme]:
            print(f"  {theme.title()}: {theme['description']}")
        print()

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
