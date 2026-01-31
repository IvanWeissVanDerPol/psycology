#!/bin/bash
# Transcribe Sarah's 252 audio files
# This uses the new unified transcription system

set -e

echo "=========================================="
echo "Transcribing Sarah Audio Files"
echo "=========================================="
echo ""

# Create output directory
mkdir -p "SOURCE_OF_TRUTH/voice_note_transcripts/Sarah"

echo "Starting transcription of 252 audio files..."
echo "This will take approximately 2-3 hours"
echo ""

# Use the unified CLI with parallel processing
python src/transcribe.py parallel \
    --chat "WhatsApp Chat with Sarah" \
    --workers 4 \
    --model base \
    --language es

echo ""
echo "=========================================="
echo "Transcription Complete!"
echo "=========================================="
echo "Output: SOURCE_OF_TRUTH/voice_note_transcripts/Sarah/"
echo ""