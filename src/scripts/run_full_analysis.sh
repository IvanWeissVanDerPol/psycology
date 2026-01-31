#!/bin/bash
# Run full transcription and analysis pipeline
# Usage: ./run_full_analysis.sh
#
# This script now uses the new unified transcription system

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "=========================================="
echo "Voice Note Transcription & Analysis"
echo "=========================================="
echo ""

# Configuration
EXPECTED_CHATS=6  # Ara, Cookie, Jonatan, Laura, Lourdes, Magali
TRANSCRIPTS_DIR="$PROJECT_DIR/SOURCE_OF_TRUTH/voice_note_transcripts"

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
if ! command -v python &> /dev/null; then
    print_error "Python not found. Please install Python 3.11 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
print_info "Using Python $PYTHON_VERSION"

# Check if required packages are installed
if ! python -c "import whisper" 2>/dev/null; then
    print_warn "Whisper not installed. Installing requirements..."
    pip install -r requirements.txt || {
        print_error "Failed to install requirements"
        exit 1
    }
fi

# Check if transcription is complete
TRANSCRIPT_COUNT=0
if [ -d "$TRANSCRIPTS_DIR" ]; then
    TRANSCRIPT_COUNT=$(find "$TRANSCRIPTS_DIR" -name "transcripts.json" 2>/dev/null | wc -l)
fi

print_info "Found $TRANSCRIPT_COUNT/$EXPECTED_CHATS chat transcripts"

# Step 1: Transcription
if [ "$TRANSCRIPT_COUNT" -lt "$EXPECTED_CHATS" ]; then
    print_info "Step 1: Running transcription..."
    echo "This will take 4-5 hours for all 5,605 voice notes."
    echo ""
    
    # Use new unified CLI
    python src/transcribe.py all --model base || {
        print_error "Transcription failed with exit code $?"
        exit 1
    }
    
    print_info "Transcription complete!"
else
    print_info "Step 1: Transcription already complete ($TRANSCRIPT_COUNT chats found)"
    print_info "To re-transcribe, run: python src/transcribe.py all --force"
fi

# Step 2: Quality check
print_info "Step 2: Checking transcript quality..."
python src/transcribe.py check || {
    print_warn "Quality check found issues (see SOURCE_OF_TRUTH/QUALITY_ISSUES.md)"
}

# Step 3: Psychological analysis
echo ""
print_info "Step 3: Running psychological analysis..."
python src/extract_psychology.py || {
    print_error "Psychological analysis failed with exit code $?"
    exit 1
}

# Final summary
echo ""
echo "=========================================="
echo "Pipeline Complete!"
echo "=========================================="
print_info "Transcripts: SOURCE_OF_TRUTH/voice_note_transcripts/"
print_info "Analysis:    SOURCE_OF_TRUTH/DEEP_EXTRACTION_REPORT.md"
print_info "Categories:  SOURCE_OF_TRUTH/CATEGORY_EXTRACTION.json"
print_info "Quality:     SOURCE_OF_TRUTH/QUALITY_ISSUES.md"
echo ""
print_info "To check status anytime, run:"
echo "  python src/transcribe.py status"
echo ""

exit 0
