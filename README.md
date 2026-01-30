# Ivan - Psychological Repository

> **Purpose:** Comprehensive psychological documentation and self-understanding  
> **Created:** January 2026  
> **Status:** Living Document

---

## Repository Structure

```
psycology/
├── SOURCE_OF_TRUTH/
│   └── MASTER_PROFILE.md          # Consolidated single source of truth
│
├── REPORTS/
│   ├── original_documents/        # Source documents
│   │   ├── Complete_Psychological_Analysis_Jan2026.md
│   │   └── A_Letter_to_My_Masters_Brahm.md
│   └── session_notes/             # Future therapy session notes
│
├── CORE_PSYCHOLOGY/
│   ├── wounds/                    # Core wounds analysis
│   │   ├── 01_PESADO_LABEL.md
│   │   ├── 02_LIPSTICK_INCIDENT.md
│   │   ├── 03_PARENTAL_DYNAMICS.md
│   │   └── 04_TOUCH_STARVATION.md
│   ├── defense_mechanisms/        # How I protect myself
│   │   ├── THE_FIXER.md
│   │   ├── THE_FIREWALL.md
│   │   ├── THE_MASK.md
│   │   └── THE_FREEZE.md
│   └── attachment_patterns/       # How I attach to others
│       └── ATTACHMENT_OVERVIEW.md
│
├── RELATIONSHIPS/
│   ├── history/                   # Past relationships
│   │   └── RELATIONSHIP_TIMELINE.md
│   └── patterns/                  # Identified patterns
│       └── IDENTIFIED_PATTERNS.md
│
├── KINK_AND_INTIMACY/
│   ├── permission_structures/     # How kink enables vulnerability
│   │   └── HOW_KINK_FUNCTIONS.md
│   └── preferences/               # Detailed preferences
│       └── COMPLETE_PREFERENCES.md
│
├── TREATMENT/
│   ├── goals/                     # Treatment targets
│   │   └── TREATMENT_GOALS.md
│   └── progress/                  # Future progress tracking
│
└── QUICK_REFERENCE/
    ├── FOR_CLINICIANS.md          # Quick ref for therapists
    └── FOR_PARTNERS.md            # Quick ref for partners/intimates
```

---

## Where to Start

| If You Are... | Start Here |
|---------------|-----------|
| A therapist | [Quick Reference for Clinicians](QUICK_REFERENCE/FOR_CLINICIANS.md) |
| A partner/intimate | [Quick Reference for Partners](QUICK_REFERENCE/FOR_PARTNERS.md) |
| Ivan (reviewing) | [Master Profile](SOURCE_OF_TRUTH/MASTER_PROFILE.md) |
| Deep diving | [Core Wounds](CORE_PSYCHOLOGY/wounds/) |

---

## Key Concepts

### The Dual-System Model

| The Engineer (Armor) | Brahm (Authentic Self) |
|---------------------|------------------------|
| Analytical, competent | Soft, vulnerable |
| Logical, guarded | Needy, tactile |
| "Be useful" | "Let me be held" |
| Default mode | Requires permission |

### Core Wounds

1. **"Pesado" Label** - Called annoying/burden by entire family
2. **Lipstick Incident** - Origin of the Information Firewall
3. **Father: "Do Not Disturb"** - Emotionally unavailable
4. **Mother: "Unpredictable Manager"** - High variance behavior
5. **Touch Starvation** - Chronic unmet need for physical affection

### Defense Mechanisms

1. **The Fixer** - Compulsive over-functioning
2. **The Firewall** - Information compartmentalization
3. **The Mask** - "Chill guy" presentation
4. **The Freeze** - Numbness/shutdown response

### The Integration Goal

> *"I want to integrate the softness of Brahm into daily life as Ivan. I want to ask for care without a permission structure. I want to feel less lonely. I want to feel warm more often."*

---

## Document Conventions

- **Bold quotes** - Ivan's own words
- **Tables** - Quick reference information
- **Related Documents** - Links at bottom of each file
- **Clinical Notes** - Marked as such when present

---

## Maintenance

This is a living document. Add:
- Session notes to `REPORTS/session_notes/`
- Progress updates to `TREATMENT/progress/`
- New insights to relevant sections

Update `SOURCE_OF_TRUTH/MASTER_PROFILE.md` when significant changes occur.

---

## Closing Note

> *"I realized I use intellectualization to avoid feeling things, so I used an AI to intellectualize my feelings for me. But underneath all this analysis, there's a lonely wolf in a blizzard who still wants to be found. The cave exists - I've seen it. I just need to learn I'm allowed to stay."*

**Prognosis: Good with appropriate therapeutic engagement.**

---

## Technical Architecture

### Transcription System (v2.0)

A unified Python module for processing WhatsApp voice notes using OpenAI Whisper.

#### Project Structure

```
psycology/
├── src/
│   └── transcription/           # Main transcription module
│       ├── __init__.py
│       ├── config.py            # Configuration management
│       ├── core/
│       │   ├── __init__.py
│       │   └── engine.py        # Whisper transcription engine
│       └── utils/
│           ├── __init__.py
│           ├── io.py            # File I/O operations
│           ├── logging_utils.py # Logging configuration
│           ├── path_utils.py    # Path parsing utilities
│           └── quality.py       # Quality validation
├── src/transcribe.py            # Unified CLI entry point
├── tests/
│   └── test_transcription.py    # Test suite
├── config/                      # Configuration templates
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
└── pyproject.toml              # Project metadata
```

#### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `single` | Transcribe one chat | `python src/transcribe.py single Laura` |
| `parallel` | Multi-worker processing | `python src/transcribe.py parallel --workers 4` |
| `all` | Process all chats | `python src/transcribe.py all` |
| `resume` | Resume interrupted job | `python src/transcribe.py resume Laura` |
| `retranscribe` | Fix quality issues | `python src/transcribe.py retranscribe` |
| `check` | Quality validation | `python src/transcribe.py check` |
| `status` | View progress | `python src/transcribe.py status` |

#### Configuration

Configuration is managed via:
1. Environment variables (highest priority)
2. `.env` file in project root
3. Default values (lowest priority)

See `.env.example` for available options.

#### Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/transcription --cov-report=html
```

#### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint
flake8 src/ tests/
ruff check src/ tests/

# Type check
mypy src/
```

---

## Git Workflow

This repository uses Git for version control.

### Initial Setup

```bash
# Repository already initialized
git status
```

### Making Changes

```bash
# Check status
git status

# Stage changes
git add <files>

# Commit with descriptive message
git commit -m "feat: description of change"

# View history
git log --oneline
```

### Commit Convention

- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code restructuring
- `docs:` Documentation changes
- `test:` Test additions/changes
- `chore:` Maintenance tasks

