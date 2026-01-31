#!/usr/bin/env python3
"""
Deep Psychological Extraction from Voice Note Transcripts

This script performs comprehensive extraction of psychologically significant
content from ALL voice note transcripts in Ivan's psychology repository.

Categories of extraction:
1. Relationship dynamics (how Laura/Lourdes/etc treat Ivan)
2. Ivan's emotional expressions
3. Pattern evidence (Fixer, Mask, Freeze, Firewall)
4. Touch/affection content
5. Conflict/arguments
6. Care-giving moments (or lack thereof)
7. Self-awareness expressions
8. Future/dreams/wants
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TRANSCRIPTS_DIR = BASE_DIR / "SOURCE_OF_TRUTH" / "voice_note_transcripts"
OUTPUT_DIR = BASE_DIR / "SOURCE_OF_TRUTH"

# Comprehensive psychological search patterns
DEEP_PATTERNS = {
    # Emotional States
    "sadness_depression": [
        r"\btriste\b",
        r"\bdeprim",
        r"\bbajone",
        r"\bmal\s+(?:día|momento|onda)",
        r"\bno\s+(?:puedo|aguanto)",
        r"\bme\s+siento\s+(?:mal|solo|vacío)",
        r"\bllor",
        r"\blágrima",
        r"\bpena\b",
    ],
    "anxiety_fear": [
        r"\bmiedo\b",
        r"\bansi",
        r"\bnervi",
        r"\bpreocup",
        r"\basust",
        r"\bpánico",
        r"\bestres",
        r"\bagobiad",
    ],
    "anger_frustration": [
        r"\bbroncas?\b",
        r"\benojad",
        r"\bfrustr",
        r"\bcansa(?:d[oa]|rme)",
        r"\bharta(?:d[oa]|rme)",
        r"\bputead",
        r"\bcalient[ae]",
    ],
    "loneliness": [
        r"\bsol[oa]\b(?!\s*(?:mente|que))",
        r"\bsoledad",
        r"\bvací[oa]",
        r"\bnadie\b",
        r"\babandon",
        r"\bextrañ",
    ],
    # Relationship Dynamics
    "care_giving": [
        r"\bte\s+(?:cuido|ayudo|preparo|hago|llevo|traigo)",
        r"\bpara\s+(?:vos|ti)\b",
        r"\bsi\s+necesit",
        r"\bte\s+(?:amo|quiero|adoro)",
        r"\bcariño\b",
    ],
    "care_receiving": [
        r"\bme\s+(?:cuida|ayuda|prepara|hace|lleva|trae)",
        r"\bpara\s+mí\b",
        r"\bgracias\b",
        r"\bte\s+agradezco",
    ],
    "conflict_tension": [
        r"\bpele[ao]",
        r"\bdiscut",
        r"\bproblema\b",
        r"\bconflicto",
        r"\bmal\s+(?:humor|onda)",
        r"\bmolest",
        r"\benfad",
        r"\bse\s+fue",
        r"\bme\s+dej",
    ],
    "neglect_abandonment": [
        r"\bno\s+(?:me\s+)?(?:escuch|entiend|import|bola)",
        r"\bignor",
        r"\bdistant",
        r"\bausent",
        r"\bfrí[oa]\b",
        r"\bnada\b.*\b(?:hizo|dijo|pasó)",
    ],
    # Physical/Touch
    "physical_affection": [
        r"\babraz",
        r"\bbes[oa]",
        r"\bcaricia",
        r"\bcuddle",
        r"\bmimito",
        r"\btoque",
        r"\bcontacto",
        r"\bcalentit",
        r"\bjunt[oa]s\b",
        r"\bacurru",
        r"\bpelo\b",
        r"\bcabeza\b",
    ],
    "physical_needs": [
        r"\bnecesit.*(?:abrazo|toque|contacto)",
        r"\bquiero.*(?:abrazo|estar\s+cerca)",
        r"\bfalta.*(?:cariño|afecto|contacto)",
    ],
    "illness_medical": [
        r"\benferm",
        r"\bhospital",
        r"\bmédic",
        r"\bdolor\b",
        r"\bfiebre",
        r"\bremedio",
        r"\bpastilla",
        r"\boperación",
        r"\bfístula",
        r"\bcirugía",
    ],
    # Communication Patterns
    "asking_for_help": [
        r"\bme\s+(?:ayud|pod[eé]s)",
        r"\bnecesito\s+(?:que|ayuda)",
        r"\bpor\s+favor\b",
        r"\bte\s+pido",
    ],
    "offering_help": [
        r"\bte\s+(?:ayudo|puedo)",
        r"\bsi\s+necesit",
        r"\bavís[ae]me",
        r"\bcuent[ae]\s+conmigo",
    ],
    "deflection_minimizing": [
        r"\bno\s+(?:pasa\s+nada|importa|te\s+preocup)",
        r"\btranqui",
        r"\bchill\b",
        r"\brelax\b",
        r"\bestoy\s+bien",
        r"\btodo\s+bien",
    ],
    "self_deprecation": [
        r"\bsoy\s+(?:un[ao]?\s+)?(?:tont|estúpid|idiota|imbécil)",
        r"\bperd[oó]n\b",
        r"\bsorry\b",
        r"\bdisculp",
        r"\bmi\s+culpa",
        r"\bmal[oa]\s+(?:persona|pareja|amig)",
    ],
    # Self-Awareness
    "self_reflection": [
        r"\bme\s+d[ií]\s+cuenta",
        r"\bentend[ií]",
        r"\brealizé",
        r"\bsiempre\s+(?:hago|soy|estoy)",
        r"\bmi\s+(?:problema|issue)",
        r"\btrauma",
        r"\bpatrón",
    ],
    "family_references": [
        r"\bmi\s+(?:mamá|papá|vieja|viejo|madre|padre)",
        r"\bmis\s+(?:padres|viejos|hermano)",
        r"\bfamilia\b",
        r"\bde\s+(?:chico|pequeño|niño)",
    ],
    "wants_needs_expressed": [
        r"\bquiero\s+(?:que|ser|estar|tener)",
        r"\bnecesito\s+(?:que|ser|estar|tener)",
        r"\bme\s+(?:gustaría|encantaría)",
        r"\bojalá\b",
        r"\bdeseo\b",
    ],
    # Relationship Status
    "relationship_positive": [
        r"\bte\s+(?:amo|quiero|adoro)",
        r"\bfeli[zc]",
        r"\bhermoso",
        r"\blindo",
        r"\bbonito",
        r"\bmejor\s+(?:cosa|momento|día)",
    ],
    "relationship_negative": [
        r"\bterminar",
        r"\bseparar",
        r"\bdej[ao]r",
        r"\bno\s+(?:funciona|aguanto|puedo\s+más)",
        r"\bcansad[oa]\s+de",
        r"\bharton?",
    ],
}


def is_quality_transcript(text: str, min_words: int = 10) -> bool:
    """Check if transcript is good enough quality to use."""
    if not text or len(text.strip()) < 30:
        return False

    words = text.split()
    if len(words) < min_words:
        return False

    # Check for excessive repetition
    unique_words = set(w.lower() for w in words)
    if len(unique_words) / len(words) < 0.25:
        return False

    # Check for non-Spanish characters (transcription errors)
    non_latin = len(re.findall(r"[\u4e00-\u9fff\u0400-\u04FF\uAC00-\uD7AF]", text))
    if non_latin > 5:
        return False

    return True


def extract_context(
    text: str, match_start: int, match_end: int, context_chars: int = 150
) -> str:
    """Extract context around a match."""
    start = max(0, match_start - context_chars)
    end = min(len(text), match_end + context_chars)

    context = text[start:end]
    if start > 0:
        context = "..." + context
    if end < len(text):
        context = context + "..."

    return context.strip()


def analyze_transcript(text: str) -> dict:
    """Analyze a single transcript for all patterns."""
    results = defaultdict(list)
    text_lower = text.lower()

    for category, patterns in DEEP_PATTERNS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, text_lower):
                context = extract_context(text, match.start(), match.end())
                results[category].append(
                    {
                        "pattern": pattern,
                        "matched_text": match.group(),
                        "context": context,
                    }
                )

    return dict(results)


def process_chat(chat_name: str, transcripts: list[dict]) -> dict:
    """Process all transcripts for a chat."""
    results = {
        "chat_name": chat_name,
        "total_files": len(transcripts),
        "quality_files": 0,
        "findings": defaultdict(list),
        "date_range": None,
        "sample_quotes": [],
    }

    dates = []

    for t in transcripts:
        text = t.get("text", "")
        if not is_quality_transcript(text):
            continue

        results["quality_files"] += 1

        if t.get("date"):
            dates.append(t["date"])

        analysis = analyze_transcript(text)

        for category, matches in analysis.items():
            for match in matches:
                results["findings"][category].append(
                    {
                        "file": t["file"],
                        "date": t.get("date"),
                        "context": match["context"],
                        "pattern": match["pattern"],
                    }
                )

    if dates:
        results["date_range"] = (min(dates), max(dates))

    return results


def generate_comprehensive_report(all_results: dict) -> str:
    """Generate a comprehensive markdown report."""
    lines = [
        "# Comprehensive Voice Note Psychological Extraction",
        "",
        f"> **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "> **Method:** Deep pattern extraction across all transcripts",
        "",
        "---",
        "",
        "## Summary Statistics",
        "",
        "| Chat | Total Files | Quality Files | Key Categories |",
        "|------|-------------|---------------|----------------|",
    ]

    for chat_name, results in sorted(all_results.items()):
        key_cats = [
            cat for cat, findings in results["findings"].items() if len(findings) >= 3
        ][:3]
        key_cats_str = ", ".join(key_cats) if key_cats else "none"
        lines.append(
            f"| {chat_name} | {results['total_files']} | {results['quality_files']} | {key_cats_str} |"
        )

    lines.extend(["", "---", ""])

    # Per-chat detailed findings
    for chat_name, results in sorted(all_results.items()):
        lines.append(f"## {chat_name}")
        lines.append("")

        if results["date_range"]:
            lines.append(
                f"**Date Range:** {results['date_range'][0]} to {results['date_range'][1]}"
            )
            lines.append("")

        if not results["findings"]:
            lines.append("*No significant findings in quality transcripts.*")
            lines.append("")
            continue

        # Group by category
        for category in sorted(results["findings"].keys()):
            findings = results["findings"][category]
            if len(findings) < 2:  # Skip categories with too few findings
                continue

            lines.append(
                f"### {category.replace('_', ' ').title()} ({len(findings)} occurrences)"
            )
            lines.append("")

            # Show top 5 examples for each category
            for finding in findings[:5]:
                lines.append(f"**{finding['file']}** ({finding['date']})")
                lines.append(f"> {finding['context']}")
                lines.append("")

            if len(findings) > 5:
                lines.append(f"*... and {len(findings) - 5} more occurrences*")
                lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("DEEP PSYCHOLOGICAL EXTRACTION FROM VOICE NOTES")
    print("=" * 60)
    print()

    print("Loading transcripts...")
    all_results = {}

    for chat_dir in sorted(TRANSCRIPTS_DIR.iterdir()):
        if not chat_dir.is_dir():
            continue

        chat_name = chat_dir.name
        json_path = chat_dir / "transcripts.json"

        if not json_path.exists():
            continue

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                transcripts = json.load(f)
                valid = [t for t in transcripts if t.get("text") and not t.get("error")]
        except Exception as e:
            print(f"  Error loading {chat_name}: {e}")
            continue

        if not valid:
            continue

        print(f"  Processing {chat_name} ({len(valid)} transcripts)...")
        results = process_chat(chat_name, valid)
        all_results[chat_name] = results

        # Print summary
        total_findings = sum(len(f) for f in results["findings"].values())
        print(
            f"    -> {results['quality_files']} quality transcripts, {total_findings} findings"
        )

    print()
    print("Generating comprehensive report...")

    report = generate_comprehensive_report(all_results)

    output_path = OUTPUT_DIR / "DEEP_EXTRACTION_REPORT.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report saved to: {output_path}")

    # Generate category-specific exports
    print()
    print("Generating category exports...")

    # High-value categories to export separately
    high_value_categories = [
        "sadness_depression",
        "loneliness",
        "physical_affection",
        "physical_needs",
        "illness_medical",
        "neglect_abandonment",
        "conflict_tension",
        "self_reflection",
        "family_references",
        "wants_needs_expressed",
    ]

    category_export = {}
    for chat_name, results in all_results.items():
        for category in high_value_categories:
            if category not in results["findings"]:
                continue
            if category not in category_export:
                category_export[category] = []
            for finding in results["findings"][category]:
                category_export[category].append({"chat": chat_name, **finding})

    # Save category export
    cat_path = OUTPUT_DIR / "CATEGORY_EXTRACTION.json"
    with open(cat_path, "w", encoding="utf-8") as f:
        json.dump(category_export, f, indent=2, ensure_ascii=False)

    print(f"Category export saved to: {cat_path}")

    # Print summary of high-value findings
    print()
    print("=" * 60)
    print("HIGH-VALUE CATEGORY SUMMARY")
    print("=" * 60)
    for cat in high_value_categories:
        count = len(category_export.get(cat, []))
        if count > 0:
            print(f"  {cat}: {count} findings")

    print()
    print("Done!")


if __name__ == "__main__":
    main()
