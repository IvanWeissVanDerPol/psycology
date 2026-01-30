import json
import os
from pathlib import Path
from collections import Counter
import re

BASE_DIR = Path("SOURCE_OF_TRUTH/voice_note_transcripts")
EXTRACTION_FILE = Path("SOURCE_OF_TRUTH/CATEGORY_EXTRACTION.json")


def load_all_transcripts():
    all_transcripts = []
    for chat_dir in BASE_DIR.iterdir():
        if chat_dir.is_dir():
            json_path = chat_dir / "transcripts.json"
            if json_path.exists():
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Add chat source
                        for item in data:
                            item["chat"] = chat_dir.name
                        all_transcripts.extend(data)
                except Exception as e:
                    print(f"Error loading {json_path}: {e}")
    return all_transcripts


def load_extracted_findings():
    try:
        with open(EXTRACTION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Flatten to a set of (chat, filename) tuples
            extracted_set = set()
            for category, items in data.items():
                for item in items:
                    extracted_set.add((item["chat"], item["file"]))
            return extracted_set
    except Exception:
        return set()


def analyze_missed_insights():
    transcripts = load_all_transcripts()
    extracted_set = load_extracted_findings()

    print(f"Total transcripts: {len(transcripts)}")
    print(f"Transcripts with findings: {len(extracted_set)}")

    # 1. Find Longest Transcripts with NO findings
    missed_candidates = []
    for t in transcripts:
        if not t.get("text"):
            continue

        # Skip if already found
        if (t["chat"], t["file"]) in extracted_set:
            continue

        word_count = len(t["text"].split())
        missed_candidates.append(
            {
                "chat": t["chat"],
                "file": t["file"],
                "date": t.get("date", "Unknown"),
                "word_count": word_count,
                "text": t["text"][:150] + "...",  # Preview
            }
        )

    # Sort by word count
    missed_candidates.sort(key=lambda x: x["word_count"], reverse=True)

    print(
        "\n=== TOP 20 LONGEST TRANSCRIPTS WITHOUT FINDINGS (Potential Missed Stories) ==="
    )
    for i, item in enumerate(missed_candidates[:20]):
        print(
            f"{i + 1}. [{item['chat']}] {item['file']} ({item['word_count']} words) - {item['date']}"
        )
        print(f"   Preview: {item['text']}\n")

    # 2. Word Frequency Analysis on ALL transcripts to find missed keywords
    all_text = " ".join([t["text"] for t in transcripts if t.get("text")])
    words = re.findall(r"\w+", all_text.lower())

    # Common Spanish stop words (basic list)
    stop_words = set(
        [
            "de",
            "que",
            "y",
            "a",
            "en",
            "el",
            "la",
            "los",
            "las",
            "un",
            "una",
            "no",
            "es",
            "si",
            "me",
            "lo",
            "por",
            "para",
            "con",
            "se",
            "te",
            "mi",
            "pero",
            "o",
            "del",
            "al",
            "yo",
            "como",
            "son",
            "mas",
            "más",
            "estoy",
            "eso",
            "todo",
            "esta",
            "está",
            "porque",
            "muy",
            "así",
            "asi",
            "cuando",
            "ya",
            "ha",
            "hay",
            "sus",
            "su",
            "ni",
            "sin",
            "nos",
            "tu",
            "tus",
            "ese",
            "esa",
            "esos",
            "esas",
            "este",
            "esta",
            "esto",
            "le",
            "les",
            "era",
            "fue",
            "fui",
            "ir",
            "voy",
            "va",
            "vas",
            "van",
            "ser",
            "soy",
            "eres",
            "somos",
            "tengo",
            "tienes",
            "tiene",
            "tenemos",
            "hacer",
            "hago",
            "haces",
            "hace",
            "hacen",
            "tipo",
            "onda",
            "fla",
            "flash",
            "slash",
        ]
    )

    filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
    common_words = Counter(filtered_words).most_common(50)

    print("\n=== TOP 50 MOST FREQUENT WORDS (excluding stop words) ===")
    print("Check this list for recurring topics we might have missed:")
    for word, count in common_words:
        print(f"{word}: {count}")


if __name__ == "__main__":
    analyze_missed_insights()
