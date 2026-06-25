"""
Concept evaluator.

Measures whether the user's answer covers the required concepts
expected for a correct answer. This is the most important evaluator
for technical questions and has the highest weight.

This directly addresses the core weakness of semantic-only evaluation:
a fluent but conceptually incomplete answer can score high on semantics
but low on concept coverage. These two scores together give a far more
accurate picture than either alone.
"""

from __future__ import annotations

from ai_core.evaluation_pipeline.base_evaluator import BaseEvaluator, DimensionScore
from ai_core.shared.similarity import SimilarityCalculator
from ai_core.shared.text_processor import TextProcessor
from schemas.answer_schema import AnswerInput


class ConceptEvaluator(BaseEvaluator):
    """
    Evaluates required concept coverage in the user's answer.

    For each question, the question bank defines a list of required
    concepts and optional bonus concepts. This evaluator checks how
    many of the required concepts appear in the answer and produces
    a score and a detailed breakdown.
    """

    @property
    def dimension_name(self) -> str:
        """Dimension name for this evaluator."""
        return "concept"

    def evaluate(self, answer_input: AnswerInput) -> DimensionScore:
        """
        Check concept coverage in the user's answer.

        Args:
            answer_input: Contains user_answer, required_concepts,
                          and optional_concepts.

        Returns:
            DimensionScore with concept coverage score and breakdown.
        """
        user_answer = answer_input.user_answer.lower()
        required_concepts = answer_input.required_concepts
        optional_concepts = answer_input.optional_concepts

        # Check required concept coverage
        found_required, missing_required, required_coverage = (
            SimilarityCalculator.concept_overlap(required_concepts, user_answer)
        )

        # Check optional concept bonus
        found_optional, _, optional_coverage = (
            SimilarityCalculator.concept_overlap(optional_concepts, user_answer)
            if optional_concepts
            else ([], [], 0.0)
        )

        # Score calculation:
        # Required coverage is worth 85% of the score
        # Optional bonus is worth up to 15%
        required_score = required_coverage * 85.0
        optional_bonus = optional_coverage * 15.0
        score = self._clamp(required_score + optional_bonus)

        # Apply synonym-aware secondary pass if initial coverage is low
        if required_coverage < 1.0 and missing_required:
            score, found_required, missing_required = self._synonym_pass(
                score,
                found_required,
                missing_required,
                user_answer,
            )

        reason, evidence = self._build_explanation(
            score=score,
            found_required=found_required,
            missing_required=missing_required,
            found_optional=found_optional,
            total_required=len(required_concepts),
        )

        return DimensionScore(
            score=round(score, 2),
            label="Concept Coverage",
            reason=reason,
            evidence=evidence,
        )

    def _synonym_pass(
        self,
        current_score: float,
        found: list[str],
        missing: list[str],
        answer_text: str,
    ) -> tuple[float, list[str], list[str]]:
        """
        Secondary pass using lemmatization to catch concept synonyms.

        For example if the concept is "abstraction" but the user wrote
        "abstract", lemmatization will match them.

        Args:
            current_score: Score from primary pass.
            found: Already found concepts.
            missing: Concepts still missing.
            answer_text: User answer text.

        Returns:
            Tuple of (updated_score, updated_found, updated_missing).
        """
        answer_tokens = set(TextProcessor.preprocess(answer_text, remove_stops=False))
        newly_found = []

        for concept in missing:
            concept_tokens = set(
                TextProcessor.preprocess(concept, remove_stops=False)
            )
            if concept_tokens & answer_tokens:
                newly_found.append(concept)

        if newly_found:
            updated_found = found + newly_found
            updated_missing = [m for m in missing if m not in newly_found]
            new_coverage = len(updated_found) / max(
                len(updated_found) + len(updated_missing), 1
            )
            updated_score = self._clamp(new_coverage * 85.0)
            return updated_score, updated_found, updated_missing

        return current_score, found, missing

    def _build_explanation(
        self,
        score: float,
        found_required: list[str],
        missing_required: list[str],
        found_optional: list[str],
        total_required: int,
    ) -> tuple[str, list[str]]:
        """
        Build detailed concept coverage explanation.

        Args:
            score: Final concept score.
            found_required: Required concepts that were found.
            missing_required: Required concepts that were missing.
            found_optional: Optional bonus concepts found.
            total_required: Total required concepts count.

        Returns:
            Tuple of (reason text, evidence list).
        """
        evidence = []

        if found_required:
            evidence.append(
                f"Required concepts found ({len(found_required)}/{total_required}): "
                + ", ".join(found_required)
            )
        if missing_required:
            evidence.append(
                f"Required concepts missing ({len(missing_required)}/{total_required}): "
                + ", ".join(missing_required)
            )
        if found_optional:
            evidence.append(
                "Bonus concepts mentioned: " + ", ".join(found_optional)
            )

        coverage_ratio = len(found_required) / max(total_required, 1)

        if coverage_ratio >= 0.9:
            reason = (
                f"Excellent concept coverage. You addressed "
                f"{len(found_required)} of {total_required} required concepts. "
                + (
                    f"You also mentioned bonus concepts: {', '.join(found_optional)}."
                    if found_optional
                    else ""
                )
            )
        elif coverage_ratio >= 0.7:
            reason = (
                f"Good concept coverage. You covered {len(found_required)} of "
                f"{total_required} required concepts. "
                f"Missing: {', '.join(missing_required)}. "
                f"Strengthen your answer by including these."
            )
        elif coverage_ratio >= 0.5:
            reason = (
                f"Partial concept coverage. Only {len(found_required)} of "
                f"{total_required} required concepts were addressed. "
                f"Missing concepts: {', '.join(missing_required)}. "
                f"These are critical for a complete answer."
            )
        elif coverage_ratio > 0:
            reason = (
                f"Weak concept coverage. Only {len(found_required)} of "
                f"{total_required} required concepts were found. "
                f"Missing: {', '.join(missing_required)}. "
                f"Review this topic before your interview."
            )
        else:
            reason = (
                f"None of the {total_required} required concepts were detected "
                f"in your answer. Required: {', '.join(missing_required)}. "
                f"Your answer may be too generic or off-topic."
            )

        return reason, evidence
