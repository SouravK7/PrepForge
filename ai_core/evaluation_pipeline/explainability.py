"""
Explainability engine.

Generates human-readable explanations for every evaluation score.
Consolidates dimension reasons into a structured explanation object.

Every score must have a human-readable reason.
No mysterious numbers.
"""

from __future__ import annotations

from ai_core.evaluation_pipeline.base_evaluator import DimensionScore
from ai_core.evaluation_pipeline.score_fusion import FusionInput
from schemas.evaluation_schema import (
    EvaluationEvidence,
    EvaluationExplanation,
    GradeEnum,
    ReadinessEnum,
)


class ExplainabilityEngine:
    """
    Consolidates per-dimension explanations into structured output.

    Takes dimension scores (each with their own reason and evidence)
    and assembles them into EvaluationExplanation and EvaluationEvidence
    schemas suitable for display to the user.
    """

    def build_explanation(
        self,
        fusion_input: FusionInput,
        grade: GradeEnum,
        readiness: ReadinessEnum,
        weighted_final: float,
    ) -> EvaluationExplanation:
        """
        Build human-readable explanation for all evaluation dimensions.

        Args:
            fusion_input: All individual dimension scores with reasons.
            grade: Final letter grade.
            readiness: Interview readiness level.
            weighted_final: Final weighted score 0-100.

        Returns:
            EvaluationExplanation with reasons for every dimension.
        """
        overall_summary = self._build_overall_summary(
            grade=grade,
            readiness=readiness,
            weighted_final=weighted_final,
            semantic_score=fusion_input.semantic.score,
            concept_score=fusion_input.concept.score,
            communication_score=fusion_input.communication.score,
            evidence_score=fusion_input.evidence.score,
            reasoning_score=fusion_input.reasoning.score,
        )

        improvement_tip = self._build_improvement_tip(
            semantic=fusion_input.semantic,
            concept=fusion_input.concept,
            communication=fusion_input.communication,
            evidence=fusion_input.evidence,
            reasoning=fusion_input.reasoning,
        )

        return EvaluationExplanation(
            semantic_reason=fusion_input.semantic.reason,
            concept_reason=fusion_input.concept.reason,
            communication_reason=fusion_input.communication.reason,
            evidence_reason=fusion_input.evidence.reason,
            reasoning_reason=fusion_input.reasoning.reason,
            overall_summary=overall_summary,
            improvement_tip=improvement_tip,
        )

    def build_evidence(
        self,
        concept_dim: DimensionScore,
        communication_dim: DimensionScore,
        evidence_dim: DimensionScore,
        reasoning_dim: DimensionScore,
        semantic_dim: DimensionScore,
    ) -> EvaluationEvidence:
        """
        Build structured evidence object from dimension scores.

        Extracts matched concepts, missing concepts, grammar issues,
        and detected examples from each dimension's evidence list.

        Args:
            concept_dim: DimensionScore from ConceptEvaluator.
            communication_dim: DimensionScore from CommunicationEvaluator.
            evidence_dim: DimensionScore from EvidenceEvaluator.
            reasoning_dim: DimensionScore from ReasoningEvaluator.
            semantic_dim: DimensionScore from SemanticEvaluator.

        Returns:
            EvaluationEvidence with structured evidence fields.
        """
        # Parse concept evidence
        matched_concepts: list[str] = []
        missing_concepts: list[str] = []
        optional_concepts_found: list[str] = []

        for ev in concept_dim.evidence:
            if "Required concepts found" in ev:
                # Parse: "Required concepts found (N/M): a, b, c"
                parts = ev.split(": ", 1)
                if len(parts) > 1:
                    matched_concepts = [c.strip() for c in parts[1].split(",")]
            elif "Required concepts missing" in ev:
                parts = ev.split(": ", 1)
                if len(parts) > 1:
                    missing_concepts = [c.strip() for c in parts[1].split(",")]
            elif "Bonus concepts mentioned" in ev:
                parts = ev.split(": ", 1)
                if len(parts) > 1:
                    optional_concepts_found = [c.strip() for c in parts[1].split(",")]

        # Parse grammar issues from communication evidence
        grammar_issues: list[str] = []
        for ev in communication_dim.evidence:
            if "fragment" in ev.lower() or "filler" in ev.lower():
                grammar_issues.append(ev)

        # Detected examples from evidence evaluator
        detected_examples = [
            ev for ev in evidence_dim.evidence
            if ev and ev != "No concrete examples detected"
        ]

        # Derive strengths and weaknesses from scores
        strengths = self._derive_strengths(
            semantic_dim=semantic_dim,
            concept_dim=concept_dim,
            communication_dim=communication_dim,
            evidence_dim=evidence_dim,
            reasoning_dim=reasoning_dim,
        )

        weaknesses = self._derive_weaknesses(
            semantic_dim=semantic_dim,
            concept_dim=concept_dim,
            communication_dim=communication_dim,
            evidence_dim=evidence_dim,
            reasoning_dim=reasoning_dim,
        )

        return EvaluationEvidence(
            matched_concepts=matched_concepts,
            missing_concepts=missing_concepts,
            optional_concepts_found=optional_concepts_found,
            detected_examples=detected_examples,
            grammar_issues=grammar_issues,
            strengths=strengths,
            weaknesses=weaknesses,
        )

    def _build_overall_summary(
        self,
        grade: GradeEnum,
        readiness: ReadinessEnum,
        weighted_final: float,
        semantic_score: float,
        concept_score: float,
        communication_score: float,
        evidence_score: float,
        reasoning_score: float,
    ) -> str:
        """
        Build one-paragraph overall summary of answer quality.

        Args:
            grade: Letter grade.
            readiness: Readiness level.
            weighted_final: Final score.
            semantic_score: Semantic similarity score.
            concept_score: Concept coverage score.
            communication_score: Communication quality score.
            evidence_score: Evidence score.
            reasoning_score: Reasoning score.

        Returns:
            Overall summary paragraph.
        """
        # Identify strongest and weakest dimensions
        scores = {
            "semantic relevance": semantic_score,
            "concept coverage": concept_score,
            "communication quality": communication_score,
            "evidence and examples": evidence_score,
            "reasoning depth": reasoning_score,
        }
        strongest = max(scores, key=lambda k: scores[k])
        weakest = min(scores, key=lambda k: scores[k])

        readiness_label = {
            ReadinessEnum.EXCELLENT: "excellent interview readiness",
            ReadinessEnum.GOOD: "good interview readiness",
            ReadinessEnum.AVERAGE: "average interview readiness",
            ReadinessEnum.POOR: "below-average interview readiness",
        }[readiness]

        return (
            f"This answer received a grade of {grade.value} "
            f"({weighted_final:.1f}/100), indicating {readiness_label}. "
            f"The strongest dimension was {strongest} "
            f"({scores[strongest]:.1f}/100), while the weakest was "
            f"{weakest} ({scores[weakest]:.1f}/100). "
            f"Overall, the answer demonstrates "
            + (
                "strong command of the topic with minor gaps to address."
                if weighted_final >= 75
                else "partial understanding with significant room for improvement."
                if weighted_final >= 50
                else "limited understanding of the topic. Focus study on core concepts."
            )
        )

    def _build_improvement_tip(
        self,
        semantic: DimensionScore,
        concept: DimensionScore,
        communication: DimensionScore,
        evidence: DimensionScore,
        reasoning: DimensionScore,
    ) -> str:
        """
        Identify the single most impactful improvement the user can make.

        Args:
            semantic: Semantic dimension score.
            concept: Concept dimension score.
            communication: Communication dimension score.
            evidence: Evidence dimension score.
            reasoning: Reasoning dimension score.

        Returns:
            Single actionable improvement tip.
        """
        scores = {
            "concept": concept.score,
            "reasoning": reasoning.score,
            "evidence": evidence.score,
            "semantic": semantic.score,
            "communication": communication.score,
        }
        weakest_dim = min(scores, key=lambda k: scores[k])

        tips = {
            "concept": (
                "Focus on memorizing and including all required concepts in "
                "your answer. Review the topic's core terminology and ensure "
                "each key term appears in your explanation."
            ),
            "reasoning": (
                "Work on explaining the 'why' and 'how' behind your statements. "
                "Use causal connectors like 'because', 'therefore', and 'this "
                "means' to demonstrate logical thinking rather than just listing facts."
            ),
            "evidence": (
                "Support your answers with concrete real-world examples. Try phrases "
                "like 'For example, in a project I built...' or reference specific "
                "technologies you have used in practice."
            ),
            "semantic": (
                "Review the core concept being tested and align your answer more "
                "closely with the expected explanation. Re-read a reference answer "
                "and identify the key ideas you missed."
            ),
            "communication": (
                "Improve answer structure using signpost words: 'First... Second... "
                "Finally...' or 'In summary...'. Aim for 3-5 clear sentences per "
                "concept you explain."
            ),
        }

        return tips.get(
            weakest_dim,
            "Review the topic broadly and practice explaining concepts out loud.",
        )

    def _derive_strengths(
        self,
        semantic_dim: DimensionScore,
        concept_dim: DimensionScore,
        communication_dim: DimensionScore,
        evidence_dim: DimensionScore,
        reasoning_dim: DimensionScore,
    ) -> list[str]:
        """
        Derive a list of strengths from high-scoring dimensions.

        Args:
            semantic_dim: Semantic score.
            concept_dim: Concept score.
            communication_dim: Communication score.
            evidence_dim: Evidence score.
            reasoning_dim: Reasoning score.

        Returns:
            List of strength descriptions.
        """
        strengths = []
        threshold = 70.0

        if semantic_dim.score >= threshold:
            strengths.append(f"Strong semantic relevance ({semantic_dim.score:.1f}/100)")
        if concept_dim.score >= threshold:
            strengths.append(f"Good concept coverage ({concept_dim.score:.1f}/100)")
        if communication_dim.score >= threshold:
            strengths.append(f"Clear communication ({communication_dim.score:.1f}/100)")
        if evidence_dim.score >= threshold:
            strengths.append(f"Good use of examples ({evidence_dim.score:.1f}/100)")
        if reasoning_dim.score >= threshold:
            strengths.append(f"Strong reasoning depth ({reasoning_dim.score:.1f}/100)")

        return strengths

    def _derive_weaknesses(
        self,
        semantic_dim: DimensionScore,
        concept_dim: DimensionScore,
        communication_dim: DimensionScore,
        evidence_dim: DimensionScore,
        reasoning_dim: DimensionScore,
    ) -> list[str]:
        """
        Derive a list of weaknesses from low-scoring dimensions.

        Args:
            semantic_dim: Semantic score.
            concept_dim: Concept score.
            communication_dim: Communication score.
            evidence_dim: Evidence score.
            reasoning_dim: Reasoning score.

        Returns:
            List of weakness descriptions.
        """
        weaknesses = []
        threshold = 50.0

        if semantic_dim.score < threshold:
            weaknesses.append(f"Low semantic relevance ({semantic_dim.score:.1f}/100)")
        if concept_dim.score < threshold:
            weaknesses.append(f"Insufficient concept coverage ({concept_dim.score:.1f}/100)")
        if communication_dim.score < threshold:
            weaknesses.append(f"Weak communication structure ({communication_dim.score:.1f}/100)")
        if evidence_dim.score < threshold:
            weaknesses.append(f"Lacks concrete examples ({evidence_dim.score:.1f}/100)")
        if reasoning_dim.score < threshold:
            weaknesses.append(f"Limited reasoning depth ({reasoning_dim.score:.1f}/100)")

        return weaknesses
