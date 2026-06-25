"""
Evidence evaluator.

Detects whether the user provided concrete real-world examples,
specific cases, or practical evidence to support their answer.
Answers with examples demonstrate deeper understanding.
"""

from __future__ import annotations

import re

from ai_core.evaluation_pipeline.base_evaluator import BaseEvaluator, DimensionScore
from ai_core.shared.text_processor import TextProcessor
from schemas.answer_schema import AnswerInput


class EvidenceEvaluator(BaseEvaluator):
    """
    Evaluates presence and quality of evidence and examples.

    Detects real-world examples, specific technology mentions,
    project references, and practical application signals.
    Answers that include concrete evidence score higher.
    """

    # Phrases that signal a real-world example is being given
    EXAMPLE_SIGNALS = [
        "for example", "for instance", "such as", "like when",
        "in my project", "in my experience", "i used", "we used",
        "i implemented", "i built", "i worked on", "in practice",
        "a real case", "in production", "at work", "when i was",
        "consider", "imagine", "suppose", "take the case",
        "in one project", "when building",
    ]

    # Specific technical terms that suggest practical knowledge
    TECHNOLOGY_SIGNALS = [
        "python", "java", "javascript", "django", "flask", "fastapi",
        "react", "docker", "kubernetes", "aws", "azure", "gcp",
        "mysql", "postgresql", "mongodb", "redis", "kafka",
        "github", "git", "rest", "graphql", "microservices",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
        "linux", "nginx", "jwt", "oauth",
    ]

    # Numeric evidence signals (specific numbers = concrete experience)
    NUMERIC_PATTERN = re.compile(
        r"\b\d+\s*(ms|seconds|minutes|hours|days|users|records|gb|mb|%)\b",
        re.IGNORECASE,
    )

    @property
    def dimension_name(self) -> str:
        """Dimension name for this evaluator."""
        return "evidence"

    def evaluate(self, answer_input: AnswerInput) -> DimensionScore:
        """
        Evaluate evidence and examples in the answer.

        Args:
            answer_input: Contains user_answer.

        Returns:
            DimensionScore with evidence quality score.
        """
        user_answer = answer_input.user_answer
        answer_lower = user_answer.lower()

        # --- Detect example signals ---
        example_signals_found = [
            signal for signal in self.EXAMPLE_SIGNALS
            if signal in answer_lower
        ]

        # --- Detect technology mentions ---
        tech_signals_found = [
            tech for tech in self.TECHNOLOGY_SIGNALS
            if tech in answer_lower
        ]

        # --- Detect numeric evidence ---
        numeric_matches = self.NUMERIC_PATTERN.findall(user_answer)

        # --- Score calculation ---
        score = self._calculate_score(
            example_signals=example_signals_found,
            tech_signals=tech_signals_found,
            numeric_matches=numeric_matches,
        )

        detected_examples = (
            [f"Example signal: '{sig}'" for sig in example_signals_found[:3]]
            + [f"Technology mentioned: '{tech}'" for tech in tech_signals_found[:3]]
            + [f"Numeric evidence: '{num}'" for num in numeric_matches[:2]]
        )

        reason, evidence = self._build_explanation(
            score=score,
            example_signals=example_signals_found,
            tech_signals=tech_signals_found,
            numeric_matches=numeric_matches,
            detected_examples=detected_examples,
        )

        return DimensionScore(
            score=round(score, 2),
            label="Evidence and Examples",
            reason=reason,
            evidence=evidence if evidence else ["No concrete examples detected"],
        )

    def _calculate_score(
        self,
        example_signals: list[str],
        tech_signals: list[str],
        numeric_matches: list[str],
    ) -> float:
        """
        Calculate evidence score from detected signals.

        Args:
            example_signals: Detected example signal phrases.
            tech_signals: Detected technology references.
            numeric_matches: Detected numeric evidence.

        Returns:
            Evidence score 0-100.
        """
        score = 0.0

        # Example signals worth up to 50 points
        if len(example_signals) >= 2:
            score += 50.0
        elif len(example_signals) == 1:
            score += 35.0

        # Technology mentions worth up to 30 points
        if len(tech_signals) >= 3:
            score += 30.0
        elif len(tech_signals) == 2:
            score += 22.0
        elif len(tech_signals) == 1:
            score += 12.0

        # Numeric evidence worth up to 20 points
        if len(numeric_matches) >= 2:
            score += 20.0
        elif len(numeric_matches) == 1:
            score += 12.0

        return self._clamp(score)

    def _build_explanation(
        self,
        score: float,
        example_signals: list[str],
        tech_signals: list[str],
        numeric_matches: list[str],
        detected_examples: list[str],
    ) -> tuple[str, list[str]]:
        """
        Build evidence quality explanation.

        Args:
            score: Final evidence score.
            example_signals: Found example phrases.
            tech_signals: Found technology references.
            numeric_matches: Found numeric evidence.
            detected_examples: Summary of detected evidence.

        Returns:
            Tuple of (reason text, evidence list).
        """
        evidence_list = detected_examples if detected_examples else []

        if score >= 80:
            reason = (
                "Strong evidence provided. Your answer includes concrete "
                "examples, specific technologies, or real-world scenarios "
                "that demonstrate practical experience and deep understanding."
            )
        elif score >= 60:
            reason = (
                "Good evidence. You referenced some specific examples or "
                "technologies. Adding more concrete details or a brief "
                "real-world scenario would strengthen your answer further."
            )
        elif score >= 40:
            reason = (
                "Some evidence provided but it is limited. Try to include "
                "at least one specific real-world example or project "
                "reference to make your answer more credible."
            )
        elif score >= 20:
            reason = (
                "Minimal evidence. Your answer stays at a theoretical level. "
                "Interviewers value candidates who can connect theory to "
                "practice. Add phrases like 'For example, in a project I built...' "
                "to demonstrate applied knowledge."
            )
        else:
            reason = (
                "No concrete evidence or examples detected. Your answer is "
                "purely theoretical. Always try to support your points with "
                "at least one specific example, technology reference, or "
                "real-world scenario from your experience."
            )

        return reason, evidence_list
