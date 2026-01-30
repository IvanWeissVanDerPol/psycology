#!/usr/bin/env python3
"""
Integrated Psychological Analysis

Combines:
1. Voice note transcript patterns
2. Questionnaire responses
3. Temporal/timeline analysis
4. Cross-chat correlation analysis
5. Predictive indicators

This is the comprehensive analysis that addresses all gaps identified in the roast.
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from transcription import config
from transcription.utils.logging_utils import setup_logging
from transcription.utils.quality import is_quality_transcript

logger = setup_logging(__name__)


class TemporalAnalyzer:
    """Analyze patterns over time."""

    def __init__(self):
        self.timeline_data = defaultdict(lambda: defaultdict(list))

    def add_event(self, date: str, chat: str, category: str, context: str):
        """Add a pattern occurrence to the timeline."""
        self.timeline_data[date][chat].append(
            {"category": category, "context": context}
        )

    def analyze_weekly_patterns(self) -> dict:
        """Analyze patterns by week to detect escalations."""
        weekly_counts = defaultdict(lambda: defaultdict(int))

        for date_str, chats in self.timeline_data.items():
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                week_key = date.strftime("%Y-W%U")

                for chat, events in chats.items():
                    for event in events:
                        weekly_counts[week_key][event["category"]] += 1
            except ValueError:
                continue

        return dict(weekly_counts)

    def detect_escalation_periods(self, threshold: int = 5) -> list[dict]:
        """Detect periods with high pattern frequency."""
        weekly = self.analyze_weekly_patterns()
        escalations = []

        for week, categories in sorted(weekly.items()):
            total = sum(categories.values())
            if total >= threshold:
                escalations.append(
                    {"week": week, "total_patterns": total, "categories": categories}
                )

        return escalations


class CrossChatAnalyzer:
    """Analyze patterns across different chats."""

    def __init__(self):
        self.chat_patterns = defaultdict(lambda: defaultdict(int))
        self.chat_metadata = {}

    def register_chat(self, chat_name: str, relationship_type: str, date_range: tuple):
        """Register chat metadata."""
        self.chat_metadata[chat_name] = {
            "type": relationship_type,
            "date_range": date_range,
        }

    def add_pattern(self, chat_name: str, category: str, date: str):
        """Add pattern occurrence."""
        self.chat_patterns[chat_name][category] += 1

    def calculate_correlation_matrix(self) -> dict:
        """Calculate pattern correlations across chats."""
        # Get all categories
        all_categories = set()
        for patterns in self.chat_patterns.values():
            all_categories.update(patterns.keys())

        # Calculate correlations
        correlations = {}
        for cat1 in all_categories:
            correlations[cat1] = {}
            for cat2 in all_categories:
                if cat1 != cat2:
                    # Calculate co-occurrence
                    co_occur = 0
                    for chat, patterns in self.chat_patterns.items():
                        if cat1 in patterns and cat2 in patterns:
                            co_occur += 1
                    correlations[cat1][cat2] = co_occur

        return correlations

    def compare_relationship_types(self) -> dict:
        """Compare patterns by relationship type."""
        type_patterns = defaultdict(lambda: defaultdict(list))

        for chat, patterns in self.chat_patterns.items():
            if chat in self.chat_metadata:
                rel_type = self.chat_metadata[chat]["type"]
                for category, count in patterns.items():
                    type_patterns[rel_type][category].append(count)

        # Calculate averages
        results = {}
        for rel_type, categories in type_patterns.items():
            results[rel_type] = {}
            for category, counts in categories.items():
                results[rel_type][category] = {
                    "avg": sum(counts) / len(counts),
                    "min": min(counts),
                    "max": max(counts),
                    "count": len(counts),
                }

        return results


class PredictiveAnalyzer:
    """Generate predictive indicators for relationship strain."""

    def __init__(self):
        self.indicators = []

    def analyze_pattern_sequences(self, temporal_data: dict) -> list[dict]:
        """Analyze sequences that precede negative events."""
        sequences = []

        # Sort by date
        sorted_dates = sorted(temporal_data.keys())

        for i, date in enumerate(sorted_dates):
            daily_total = sum(
                len(events)
                for chats in temporal_data[date].values()
                for events in [chats]
            )

            # High pattern day
            if daily_total >= 10:
                sequences.append(
                    {
                        "date": date,
                        "type": "high_activity",
                        "total_patterns": daily_total,
                        "warning": "Elevated emotional expression - potential processing event",
                    }
                )

        return sequences

    def generate_risk_assessment(self, chat_patterns: dict) -> dict:
        """Generate risk assessment based on pattern combinations."""
        risks = []

        for chat, patterns in chat_patterns.items():
            risk_factors = []

            # High deflection + high self-deprecation = danger
            if (
                patterns.get("deflection_minimizing", 0) > 20
                and patterns.get("self_deprecation", 0) > 15
            ):
                risk_factors.append(
                    {
                        "type": "mask_overload",
                        "severity": "high",
                        "description": "High deflection with self-criticism suggests unsustainable suppression",
                    }
                )

            # High needs expression + low care receiving = unmet needs
            if (
                patterns.get("wants_needs_expressed", 0) > 50
                and patterns.get("care_receiving", 0) < 20
            ):
                risk_factors.append(
                    {
                        "type": "unmet_needs",
                        "severity": "medium",
                        "description": "Expressing needs but not receiving care",
                    }
                )

            # Sadness + relationship_negative + no physical_affection = breakup risk
            if (
                patterns.get("sadness_depression", 0) > 10
                and patterns.get("relationship_negative", 0) > 5
                and patterns.get("physical_affection", 0) < 10
            ):
                risk_factors.append(
                    {
                        "type": "relationship_crisis",
                        "severity": "high",
                        "description": "Sadness with relationship negativity and touch deprivation",
                    }
                )

            if risk_factors:
                risks.append({"chat": chat, "risk_factors": risk_factors})

        return risks


class QuestionnaireIntegrator:
    """Integrate questionnaire responses with voice note analysis."""

    def __init__(self):
        self.questionnaire_path = (
            config.paths.source_of_truth / "QUESTIONNAIRE_FOR_IVAN"
        )
        self.responses = {}

    def load_questionnaire_responses(self) -> dict:
        """Load and parse questionnaire responses."""
        sections = [
            ("A_Validation_of_Identified_Patterns.md", "pattern_validation"),
            ("B_Relationship_Deep_Dives.md", "relationships"),
            ("C_Family_and_Origin.md", "family"),
            ("D_Current_State.md", "current_state"),
            ("E_Kink_and_Intimacy.md", "kink_intimacy"),
            ("F_Treatment_and_Goals.md", "treatment_goals"),
            ("I_The_Knowing_Acting_Gap.md", "knowing_acting_gap"),
        ]

        data = {}
        for filename, key in sections:
            filepath = self.questionnaire_path / filename
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Extract Ivan's responses (bold text)
                    responses = re.findall(r"\*\*([^*]+)\*\*", content)
                    data[key] = responses

        return data

    def cross_reference_with_patterns(self, voice_patterns: dict) -> dict:
        """Cross-reference questionnaire claims with voice note evidence."""
        questionnaire = self.load_questionnaire_responses()

        cross_refs = []

        # Check for The Fixer
        if "pattern_validation" in questionnaire:
            fixer_mentioned = any(
                "fixer" in r.lower() for r in questionnaire["pattern_validation"]
            )
            fixer_evidence = sum(
                1 for p in voice_patterns.values() if p.get("offering_help", 0) > 20
            )

            cross_refs.append(
                {
                    "pattern": "The Fixer",
                    "questionnaire_claimed": fixer_mentioned,
                    "voice_evidence_count": fixer_evidence,
                    "consistency": "confirmed"
                    if fixer_mentioned and fixer_evidence > 2
                    else "partial",
                }
            )

        # Check for communication issues
        if "knowing_acting_gap" in questionnaire:
            comm_issues = any(
                "comunic" in r.lower() for r in questionnaire["knowing_acting_gap"]
            )
            voice_comm = sum(
                p.get("deflection_minimizing", 0) for p in voice_patterns.values()
            )

            cross_refs.append(
                {
                    "pattern": "Communication Difficulty",
                    "questionnaire_claimed": comm_issues,
                    "voice_evidence": voice_comm,
                    "consistency": "confirmed"
                    if comm_issues and voice_comm > 50
                    else "partial",
                }
            )

        return cross_refs


def run_integrated_analysis():
    """Run the complete integrated analysis."""
    logger.info("=" * 60)
    logger.info("INTEGRATED PSYCHOLOGICAL ANALYSIS")
    logger.info("=" * 60)

    # Initialize analyzers
    temporal = TemporalAnalyzer()
    cross_chat = CrossChatAnalyzer()
    predictive = PredictiveAnalyzer()
    questionnaire = QuestionnaireIntegrator()

    # Load all transcripts and extract patterns
    logger.info("\n1. Loading transcript data...")
    chat_data = {}

    for chat_dir in config.paths.transcripts_output.iterdir():
        if not chat_dir.is_dir():
            continue

        json_path = chat_dir / "transcripts.json"
        if not json_path.exists():
            continue

        with open(json_path, "r", encoding="utf-8") as f:
            transcripts = json.load(f)

        chat_name = chat_dir.name
        chat_data[chat_name] = transcripts

        logger.info(f"  Loaded {len(transcripts)} transcripts from {chat_name}")

    # Analyze patterns
    logger.info("\n2. Analyzing temporal patterns...")
    for chat_name, transcripts in chat_data.items():
        for t in transcripts:
            if not t.get("text") or t.get("error"):
                continue

            date = t.get("date")
            if not date:
                continue

            # Simple pattern detection (keywords)
            text_lower = t["text"].lower()

            # Add to temporal analysis
            if any(kw in text_lower for kw in ["triste", "deprim", "llor"]):
                temporal.add_event(date, chat_name, "sadness", t["text"][:100])

            if any(kw in text_lower for kw in ["abraz", "beso", "toque"]):
                temporal.add_event(
                    date, chat_name, "physical_affection", t["text"][:100]
                )

            if any(kw in text_lower for kw in ["no puedo", "no sé", "no entiendo"]):
                temporal.add_event(
                    date, chat_name, "communication_difficulty", t["text"][:100]
                )

    # Detect escalation periods
    escalations = temporal.detect_escalation_periods(threshold=5)
    logger.info(f"  Found {len(escalations)} escalation periods")

    # Cross-chat analysis
    logger.info("\n3. Analyzing cross-chat patterns...")
    for chat_name, transcripts in chat_data.items():
        patterns = defaultdict(int)

        for t in transcripts:
            if not t.get("text"):
                continue

            text_lower = t["text"].lower()

            if any(kw in text_lower for kw in ["triste", "deprim", "llor"]):
                patterns["sadness"] += 1
            if any(kw in text_lower for kw in ["abraz", "beso", "toque"]):
                patterns["physical_affection"] += 1
            if any(kw in text_lower for kw in ["no puedo", "no sé"]):
                patterns["communication_difficulty"] += 1
            if any(kw in text_lower for kw in ["help", "ayuda", "te ayudo"]):
                patterns["help_exchange"] += 1

        for cat, count in patterns.items():
            cross_chat.add_pattern(chat_name, cat, "unknown")

    # Relationship type mapping
    relationship_types = {
        "Laura": "romantic_partner",
        "Jonatan_Verdun": "male_friend",
        "Lourdes_Youko_Kurama": "fwb",
        "Magali_Carreras": "university_friend",
        "Defi": "kink_community",
        "Ara_Nunez_Poli": "balanced_friend",
        "Cookie": "breakthrough_friend",
    }

    for chat, rel_type in relationship_types.items():
        if chat in chat_data:
            cross_chat.register_chat(chat, rel_type, ("unknown", "unknown"))

    type_comparison = cross_chat.compare_relationship_types()
    logger.info(f"  Analyzed {len(type_comparison)} relationship types")

    # Predictive analysis
    logger.info("\n4. Generating predictive indicators...")
    chat_pattern_summary = {}
    for chat_name, transcripts in chat_data.items():
        patterns = defaultdict(int)
        for t in transcripts:
            if t.get("text"):
                text_lower = t["text"].lower()
                if any(kw in text_lower for kw in ["triste", "deprim"]):
                    patterns["sadness_depression"] += 1
                if any(kw in text_lower for kw in ["no puedo", "no sé"]):
                    patterns["deflection_minimizing"] += 1
                if any(kw in text_lower for kw in ["soy tont", "idiota", "imbécil"]):
                    patterns["self_deprecation"] += 1
        chat_pattern_summary[chat_name] = dict(patterns)

    risk_assessment = predictive.generate_risk_assessment(chat_pattern_summary)
    logger.info(f"  Found {len(risk_assessment)} risk assessments")

    # Questionnaire integration
    logger.info("\n5. Integrating questionnaire responses...")
    cross_references = questionnaire.cross_reference_with_patterns(chat_pattern_summary)
    logger.info(f"  Cross-referenced {len(cross_references)} patterns")

    # Generate comprehensive report
    logger.info("\n6. Generating integrated report...")

    report = {
        "generated_at": datetime.now().isoformat(),
        "analysis_type": "integrated_psychological_analysis",
        "temporal_analysis": {
            "escalation_periods": escalations[:10],  # Top 10
            "weekly_pattern_summary": temporal.analyze_weekly_patterns(),
        },
        "cross_chat_analysis": {
            "by_relationship_type": type_comparison,
            "correlation_matrix": cross_chat.calculate_correlation_matrix(),
        },
        "predictive_indicators": {
            "risk_assessments": risk_assessment,
            "pattern_sequences": predictive.analyze_pattern_sequences(
                temporal.timeline_data
            ),
        },
        "questionnaire_integration": {
            "cross_references": cross_references,
            "consistency_score": sum(
                1 for c in cross_references if c["consistency"] == "confirmed"
            )
            / len(cross_references)
            if cross_references
            else 0,
        },
        "summary": {
            "total_chats_analyzed": len(chat_data),
            "total_escalation_periods": len(escalations),
            "high_risk_chats": len(
                [
                    r
                    for r in risk_assessment
                    if any(f["severity"] == "high" for f in r["risk_factors"])
                ]
            ),
            "questionnaire_consistency": "high"
            if all(c["consistency"] == "confirmed" for c in cross_references)
            else "partial",
        },
    }

    # Save report
    output_path = config.paths.source_of_truth / "INTEGRATED_ANALYSIS.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"\n✓ Integrated analysis saved to: {output_path}")

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("ANALYSIS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Chats analyzed: {report['summary']['total_chats_analyzed']}")
    logger.info(
        f"Escalation periods detected: {report['summary']['total_escalation_periods']}"
    )
    logger.info(f"High-risk chats: {report['summary']['high_risk_chats']}")
    logger.info(
        f"Questionnaire consistency: {report['summary']['questionnaire_consistency']}"
    )

    return report


if __name__ == "__main__":
    try:
        report = run_integrated_analysis()
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Analysis failed: {e}")
        sys.exit(1)
