# Voice Note Transcription Scripts

Scripts for transcribing WhatsApp voice notes using OpenAI Whisper (local).

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `openai-whisper` - Local transcription engine
- `torch` - PyTorch (required by Whisper)
- `tqdm` - Progress bars

### 2. First Run (Downloads Model)

On first run, Whisper will download the model (~140MB for 'base').

## Usage

### Transcribe All Voice Notes

```bash
python transcribe_voice_notes.py
```

### Transcribe Specific Chat

```bash
python transcribe_voice_notes.py --chat Laura
python transcribe_voice_notes.py --chat Cookie
```

### Use Different Model (Accuracy vs Speed)

```bash
# Faster, less accurate
python transcribe_voice_notes.py --model tiny

# Default (recommended)
python transcribe_voice_notes.py --model base

# Better accuracy, slower
python transcribe_voice_notes.py --model medium

# Best accuracy, very slow (requires ~10GB RAM)
python transcribe_voice_notes.py --model large
```

### Resume Interrupted Transcription

```bash
python transcribe_voice_notes.py --resume
```

### Preview Without Transcribing

```bash
python transcribe_voice_notes.py --dry-run
```

## Output

Transcripts are saved to:
```
SOURCE_OF_TRUTH/voice_note_transcripts/
├── Laura/
│   ├── transcripts.json    # Full data with timestamps
│   └── transcripts.md      # Human-readable, organized by date
├── Cookie/
│   ├── transcripts.json
│   └── transcripts.md
└── ...
```

## Voice Note Inventory

| Chat | Count | Est. Time (base model) |
|------|-------|------------------------|
| Laura | 2,918 | ~2-3 hours |
| Jonatan | 1,196 | ~1 hour |
| Lourdes | 1,038 | ~45 min |
| Magali | 438 | ~20 min |
| Ara | 12 | ~1 min |
| Cookie | 3 | ~10 sec |
| **TOTAL** | **5,605** | **~4-5 hours** |

## Tips

1. **Start with Cookie** (3 files) to test the setup
2. **Use GPU** if available - much faster (set `CUDA_VISIBLE_DEVICES=0`)
3. **Run overnight** for the full corpus
4. **Use `--resume`** if interrupted - won't re-transcribe completed files

## Troubleshooting

### "CUDA out of memory"
Use a smaller model: `--model tiny` or `--model base`

### "ffmpeg not found"
Install ffmpeg:
- Windows: `choco install ffmpeg` or download from https://ffmpeg.org
- Mac: `brew install ffmpeg`
- Linux: `apt install ffmpeg`

### Transcription is very slow
- CPU transcription is inherently slow
- Use `--model tiny` for speed
- Or use GPU if available
