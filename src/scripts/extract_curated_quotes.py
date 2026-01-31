#!/usr/bin/env python3
"""
Extract Curated Psychological Quotes from Voice Note Transcripts

This script searches for psychologically significant quotes based on:
1. Medical/fistula incident (Laura relationship)
2. Loneliness/soledad expressions
3. Touch starvation (abrazo, caricia, etc.)
4. "Pesado" wound echoes (burden, molesto)
5. The Fixer pattern (ayudo, te hago)
6. Vulnerability moments (lloro, miedo, triste)
7. The Mask (no pasa nada, tranqui)

Outputs clean, curated quotes for MASTER_PROFILE.md
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TRANSCRIPTS_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "voice_note_transcripts"
OUTPUT_DIR = BASE_DIR / "SOURCE_OF_TRUTH"

# Psychological search patterns - more specific than the automated script
SEARCH_CATEGORIES = {
    "fistula_medical": {
        "patterns": [
            r"fistula",
            r"enferm[oa]",
            r"hospital",
            r"médico",
            r"operación",
            r"cirugía",
            r"dolor físico",
            r"me duele",
            r"estoy mal",
            r"me siento mal",
        ],
        "description": "Medical/illness references - seeking fistula incident",
        "priority_chats": ["Laura"],
    },
    "loneliness": {
        "patterns": [
            r"\bsol[oa]\b",
            r"soledad",
            r"lonely",
            r"vacío",
            r"nadie me",
            r"no tengo a nadie",
            r"extraño",
            r"me falta",
        ],
        "description": "Expressions of loneliness",
        "priority_chats": ["Laura", "Jonatan_Verdun", "Lourdes_Youko_Kurama"],
    },
    "touch_starvation": {
        "patterns": [
            r"abrazo",
            r"abrázame",
            r"caricia",
            r"toque",
            r"cariño",
            r"contacto",
            r"cuddle",
            r"touch",
            r"mimito",
            r"piel",
            r"calor humano",
            r"calient[eo]",
        ],
        "description": "Touch/physical affection needs",
        "priority_chats": ["Jonatan_Verdun", "Lourdes_Youko_Kurama"],
    },
    "pesado_wound": {
        "patterns": [
            r"pesad[oa]",
            r"molest",
            r"inchabola",
            r"carga",
            r"burden",
            r"estorbo",
            r"sorry por",
            r"perdón por",
            r"perdona si",
            r"disculpa si",
            r"no quiero molestar",
        ],
        "description": "'Pesado' wound - fear of being a burden",
        "priority_chats": None,  # All chats
    },
    "fixer_pattern": {
        "patterns": [
            r"te ayudo",
            r"puedo ayudar",
            r"necesitas algo",
            r"te hago",
            r"te preparo",
            r"te cocino",
            r"te llevo",
            r"avísame si",
            r"cuenta conmigo",
            r"para lo que necesites",
        ],
        "description": "The Fixer in action - service orientation",
        "priority_chats": ["Jonatan_Verdun", "Magali_Carreras"],
    },
    "vulnerability": {
        "patterns": [
            r"llor[oa]",
            r"lloré",
            r"llorando",
            r"miedo",
            r"asust",
            r"triste",
            r"me duele",
            r"dolor",
            r"sufr",
            r"mal día",
            r"deprim",
            r"ansiedad",
        ],
        "description": "Direct vulnerability expressions",
        "priority_chats": ["Jonatan_Verdun", "Laura"],
    },
    "the_mask": {
        "patterns": [
            r"no pasa nada",
            r"tranqui",
            r"todo bien",
            r"estoy bien",
            r"no te preocupes",
            r"no importa",
            r"da igual",
            r"chill",
            r"relax",
        ],
        "description": "The Mask - deflection/minimizing",
        "priority_chats": None,
    },
    "pattern_recreation": {
        "patterns": [
            r"igual que mi",
            r"como mi mamá",
            r"como mi papá",
            r"mismo patrón",
            r"recreando",
            r"repitiendo",
            r"lo mismo que",
        ],
        "description": "Pattern recreation awareness",
        "priority_chats": ["Laura", "Jonatan_Verdun"],
    },
}


def is_clean_transcript(text: str) -> bool:
    """Check if transcript is clean enough to use."""
    if not text or len(text) < 30:
        return False

    # Check for excessive repetition (bad transcription artifact)
    words = text.split()
    if len(words) < 5:
        return False

    # Check for word repetition ratio
    unique_words = set(words)
    if len(unique_words) / len(words) < 0.3:  # Too many repeated words
        return False

    # Check for nonsense characters/mixed languages (transcription error)
    nonsense_patterns = [
        r"[\u4e00-\u9fff]",  # Chinese characters
        r"[\u0400-\u04FF]",  # Cyrillic
        r"[\uAC00-\uD7AF]",  # Korean
        r"[ぁ-んァ-ン]",  # Japanese
    ]
    for pattern in nonsense_patterns:
        if re.search(pattern, text):
            return False

    return True


def extract_quotes_for_category(
    transcripts: list[dict], patterns: list[str], max_quotes: int = 10
) -> list[dict]:
    """Extract clean quotes matching patterns."""
    matches = []

    for t in transcripts:
        text = t.get("text", "")
        if not is_clean_transcript(text):
            continue

        text_lower = text.lower()
        matched_patterns = []

        for pattern in patterns:
            if re.search(pattern, text_lower):
                matched_patterns.append(pattern)

        if matched_patterns:
            # Get context around the match
            match_obj = re.search(matched_patterns[0], text_lower)
            if match_obj:
                start = max(0, match_obj.start() - 100)
                end = min(len(text), match_obj.end() + 200)
                context = text[start:end]
                if start > 0:
                    context = "..." + context
                if end < len(text):
                    context = context + "..."

                matches.append(
                    {
                        "file": t["file"],
                        "date": t.get("date", "unknown"),
                        "matched_patterns": matched_patterns,
                        "context": context,
                        "full_text": text[:500] + ("..." if len(text) > 500 else ""),
                        "word_count": len(text.split()),
                    }
                )

    # Sort by word count (prefer longer, more substantial quotes)
    matches.sort(key=lambda x: x["word_count"], reverse=True)
    return matches[:max_quotes]


def load_all_transcripts() -> dict[str, list[dict]]:
    """Load all transcripts from JSON files."""
    transcripts = {}

    for chat_dir in TRANSCRIPTS_DIR.iterdir():
        if not chat_dir.is_dir():
            continue

        chat_name = chat_dir.name
        json_path = chat_dir / "transcripts.json"

        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    valid = [t for t in data if t.get("text") and not t.get("error")]
                    if valid:
                        transcripts[chat_name] = valid
                        print(f"  Loaded {chat_name}: {len(valid)} transcripts")
            except Exception as e:
                print(f"  Error loading {chat_name}: {e}")

    return transcripts


def generate_curated_report(all_results: dict) -> str:
    """Generate the curated quotes markdown report."""
    lines = [
        "# Curated Psychological Quotes from Voice Notes",
        "",
        f"> **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
        "> **Purpose:** Clean, usable quotes for psychological documentation  ",
        "> **Source:** Voice note transcripts (Whisper turbo model)",
        "",
        "These quotes are manually filtered for transcription quality and psychological significance.",
        "",
        "---",
        "",
    ]

    for category, data in all_results.items():
        cat_info = SEARCH_CATEGORIES[category]
        lines.append(f"## {category.replace('_', ' ').title()}")
        lines.append("")
        lines.append(f"*{cat_info['description']}*")
        lines.append("")

        if not data["quotes"]:
            lines.append("*No clean quotes found for this category.*")
            lines.append("")
            lines.append("---")
            lines.append("")
            continue

        for chat_name, quotes in data["quotes"].items():
            if not quotes:
                continue

            lines.append(f"### {chat_name}")
            lines.append("")

            for q in quotes:
                lines.append(f"**{q['file']}** ({q['date']})")
                lines.append(f"*Matched: {', '.join(q['matched_patterns'][:3])}*")
                lines.append("")
                lines.append(f"> {q['context']}")
                lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    print("Loading transcripts...")
    transcripts = load_all_transcripts()

    if not transcripts:
        print("No transcripts found!")
        return

    print(f"\nSearching {len(transcripts)} chats for psychological quotes...")

    all_results = {}

    for category, cat_info in SEARCH_CATEGORIES.items():
        print(f"\n  Processing: {category}")
        patterns = cat_info["patterns"]
        priority_chats = cat_info.get("priority_chats")

        category_quotes = {}

        for chat_name, chat_transcripts in transcripts.items():
            # If priority chats specified, only search those
            if priority_chats and chat_name not in priority_chats:
                continue

            quotes = extract_quotes_for_category(
                chat_transcripts, patterns, max_quotes=5
            )
            if quotes:
                category_quotes[chat_name] = quotes
                print(f"    {chat_name}: {len(quotes)} quotes")

        all_results[category] = {
            "description": cat_info["description"],
            "quotes": category_quotes,
        }

    # Generate report
    report = generate_curated_report(all_results)

    output_path = OUTPUT_DIR / "CURATED_QUOTES.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n\nReport saved to: {output_path}")

    # Print summary
    print("\n=== SUMMARY ===")
    total_quotes = 0
    for category, data in all_results.items():
        cat_count = sum(len(q) for q in data["quotes"].values())
        total_quotes += cat_count
        if cat_count > 0:
            print(f"  {category}: {cat_count} quotes")
    print(f"\n  TOTAL: {total_quotes} curated quotes")


if __name__ == "__main__":
    main()
