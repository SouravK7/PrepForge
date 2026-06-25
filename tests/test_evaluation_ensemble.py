"""
Tests for the evaluation ensemble.

Covers all 5 evaluators, score fusion, explainability,
and the full orchestrator pipeline end-to-end.
"""

from __future__ import annotations

import pytest

from schemas.answer_schema import AnswerInput
from schemas.evaluation_schema import GradeEnum, ReadinessEnum
from schemas.question_schema import QuestionType


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def technical_answer_good() -> AnswerInput:
    """A strong technical answer about OOP with good concept coverage."""
    return AnswerInput(
        session_id=1,
        user_id=1,
        question_id="q_oop_001",
        competency_id="comp_oop",
        question_text="Explain the four pillars of OOP.",
        question_type=QuestionType.TECHNICAL,
        sample_answer=(
            "The four pillars of OOP are encapsulation, inheritance, "
            "polymorphism, and abstraction. Encapsulation bundles data and "
            "methods together. Inheritance allows classes to extend others. "
            "Polymorphism enables different types to be treated uniformly. "
            "Abstraction hides implementation details."
        ),
        required_concepts=[
            "encapsulation", "inheritance", "polymorphism", "abstraction"
        ],
        optional_concepts=["interface", "class", "object"],
        rubric_id="rubric_technical_01",
        user_answer=(
            "The four pillars of OOP are encapsulation, inheritance, "
            "polymorphism, and abstraction. Encapsulation is about bundling "
            "data with methods. Inheritance allows one class to extend another. "
            "Polymorphism lets objects of different types be used through a "
            "common interface. Abstraction hides the implementation details "
            "from the user. For example, in Python I used these concepts when "
            "building a class hierarchy for a banking system."
        ),
    )


@pytest.fixture
def technical_answer_poor() -> AnswerInput:
    """A very weak technical answer with almost no concept coverage."""
    return AnswerInput(
        session_id=1,
        user_id=1,
        question_id="q_oop_001",
        competency_id="comp_oop",
        question_text="Explain the four pillars of OOP.",
        question_type=QuestionType.TECHNICAL,
        sample_answer=(
            "The four pillars of OOP are encapsulation, inheritance, "
            "polymorphism, and abstraction."
        ),
        required_concepts=[
            "encapsulation", "inheritance", "polymorphism", "abstraction"
        ],
        optional_concepts=[],
        rubric_id="rubric_technical_01",
        user_answer="OOP is a programming paradigm.",
    )


@pytest.fixture
def hr_answer_good() -> AnswerInput:
    """A good HR behavioral answer."""
    return AnswerInput(
        session_id=2,
        user_id=1,
        question_id="q_hr_001",
        competency_id="comp_teamwork",
        question_text="Tell me about a time you handled a conflict in a team.",
        question_type=QuestionType.HR,
        sample_answer=(
            "I once had a conflict with a teammate over code review feedback. "
            "I scheduled a one-on-one meeting to discuss our concerns. "
            "We agreed on a shared set of review guidelines and the conflict "
            "was resolved professionally. The outcome improved team cohesion."
        ),
        required_concepts=["conflict", "resolution", "communication"],
        optional_concepts=["team", "outcome"],
        rubric_id="rubric_hr_01",
        user_answer=(
            "In my previous project, I had a conflict with a colleague because "
            "we disagreed on the architecture. I scheduled a meeting to discuss "
            "both approaches. We compared the trade-offs and finally agreed on "
            "a hybrid solution. As a result, the project was delivered on time "
            "and the team communication improved significantly. I believe "
            "conflict resolution requires empathy and clear communication."
        ),
    )


# ---------------------------------------------------------------------------
# SemanticEvaluator tests
# ---------------------------------------------------------------------------

class TestSemanticEvaluator:
    """Tests for SemanticEvaluator."""

    def test_good_answer_high_score(self, technical_answer_good: AnswerInput) -> None:
        """A relevant answer should score above 50 on semantic."""
        from ai_core.evaluation_pipeline.semantic_evaluator import SemanticEvaluator
        evaluator = SemanticEvaluator()
        result = evaluator.evaluate(technical_answer_good)
        assert result.score >= 50.0, f"Expected high semantic score, got {result.score}"

    def test_poor_answer_lower_score(
        self, technical_answer_good: AnswerInput, technical_answer_poor: AnswerInput
    ) -> None:
        """Poor answer should score lower than good answer."""
        from ai_core.evaluation_pipeline.semantic_evaluator import SemanticEvaluator
        evaluator = SemanticEvaluator()
        good_score = evaluator.evaluate(technical_answer_good).score
        poor_score = evaluator.evaluate(technical_answer_poor).score
        assert good_score > poor_score

    def test_returns_dimension_score(self, technical_answer_good: AnswerInput) -> None:
        """Result must be a DimensionScore with required fields."""
        from ai_core.evaluation_pipeline.base_evaluator import DimensionScore
        from ai_core.evaluation_pipeline.semantic_evaluator import SemanticEvaluator
        evaluator = SemanticEvaluator()
        result = evaluator.evaluate(technical_answer_good)
        assert isinstance(result, DimensionScore)
        assert result.label == "Semantic Relevance"
        assert len(result.reason) > 10
        assert len(result.evidence) >= 2

    def test_score_in_valid_range(self, technical_answer_good: AnswerInput) -> None:
        """Score must be between 0 and 100."""
        from ai_core.evaluation_pipeline.semantic_evaluator import SemanticEvaluator
        evaluator = SemanticEvaluator()
        result = evaluator.evaluate(technical_answer_good)
        assert 0.0 <= result.score <= 100.0

    def test_dimension_name(self) -> None:
        """Dimension name must be 'semantic'."""
        from ai_core.evaluation_pipeline.semantic_evaluator import SemanticEvaluator
        evaluator = SemanticEvaluator()
        assert evaluator.dimension_name == "semantic"


# ---------------------------------------------------------------------------
# ConceptEvaluator tests
# ---------------------------------------------------------------------------

class TestConceptEvaluator:
    """Tests for ConceptEvaluator."""

    def test_all_concepts_present_high_score(
        self, technical_answer_good: AnswerInput
    ) -> None:
        """Answer with all required concepts should score high."""
        from ai_core.evaluation_pipeline.concept_evaluator import ConceptEvaluator
        evaluator = ConceptEvaluator()
        result = evaluator.evaluate(technical_answer_good)
        assert result.score >= 70.0, f"Expected high concept score, got {result.score}"

    def test_no_concepts_low_score(self, technical_answer_poor: AnswerInput) -> None:
        """Answer with no required concepts should score low."""
        from ai_core.evaluation_pipeline.concept_evaluator import ConceptEvaluator
        evaluator = ConceptEvaluator()
        result = evaluator.evaluate(technical_answer_poor)
        assert result.score < 40.0, f"Expected low concept score, got {result.score}"

    def test_evidence_contains_found_concepts(
        self, technical_answer_good: AnswerInput
    ) -> None:
        """Evidence must list found required concepts."""
        from ai_core.evaluation_pipeline.concept_evaluator import ConceptEvaluator
        evaluator = ConceptEvaluator()
        result = evaluator.evaluate(technical_answer_good)
        found_evidence = [e for e in result.evidence if "Required concepts found" in e]
        assert len(found_evidence) >= 1

    def test_partial_concept_coverage(self) -> None:
        """Answer with partial concepts should score between 0 and 85."""
        from ai_core.evaluation_pipeline.concept_evaluator import ConceptEvaluator
        partial_answer = AnswerInput(
            session_id=1,
            user_id=1,
            question_id="q_oop_001",
            competency_id="comp_oop",
            question_text="Explain OOP pillars.",
            question_type=QuestionType.TECHNICAL,
            sample_answer="Encapsulation, inheritance, polymorphism, abstraction.",
            required_concepts=["encapsulation", "inheritance", "polymorphism", "abstraction"],
            optional_concepts=[],
            rubric_id="rubric_technical_01",
            user_answer="I know about encapsulation and inheritance only.",
        )
        evaluator = ConceptEvaluator()
        result = evaluator.evaluate(partial_answer)
        assert 0.0 < result.score < 85.0

    def test_dimension_name(self) -> None:
        """Dimension name must be 'concept'."""
        from ai_core.evaluation_pipeline.concept_evaluator import ConceptEvaluator
        assert ConceptEvaluator().dimension_name == "concept"


# ---------------------------------------------------------------------------
# CommunicationEvaluator tests
# ---------------------------------------------------------------------------

class TestCommunicationEvaluator:
    """Tests for CommunicationEvaluator."""

    def test_well_structured_answer_scores_high(
        self, technical_answer_good: AnswerInput
    ) -> None:
        """A well-structured multi-sentence answer should score above 50."""
        from ai_core.evaluation_pipeline.communication_evaluator import CommunicationEvaluator
        evaluator = CommunicationEvaluator()
        result = evaluator.evaluate(technical_answer_good)
        assert result.score >= 50.0, f"Expected decent communication score, got {result.score}"

    def test_short_answer_scores_lower(self) -> None:
        """A very short answer should score lower than a full answer."""
        from ai_core.evaluation_pipeline.communication_evaluator import CommunicationEvaluator
        short_answer = AnswerInput(
            session_id=1,
            user_id=1,
            question_id="q_oop_001",
            competency_id="comp_oop",
            question_text="Explain OOP.",
            question_type=QuestionType.TECHNICAL,
            sample_answer="Encapsulation, inheritance, polymorphism, abstraction.",
            required_concepts=[],
            optional_concepts=[],
            rubric_id="rubric_technical_01",
            user_answer="OOP is good.",
        )
        evaluator = CommunicationEvaluator()
        short_score = evaluator.evaluate(short_answer).score
        good_score = evaluator.evaluate(AnswerInput(
            session_id=1,
            user_id=1,
            question_id="q_oop_001",
            competency_id="comp_oop",
            question_text="Explain OOP.",
            question_type=QuestionType.TECHNICAL,
            sample_answer="Encapsulation, inheritance, polymorphism.",
            required_concepts=[],
            optional_concepts=[],
            rubric_id="rubric_technical_01",
            user_answer=(
                "OOP has four pillars: encapsulation, inheritance, "
                "polymorphism, and abstraction. First, encapsulation "
                "bundles data together. Second, inheritance allows reuse. "
                "Finally, polymorphism enables flexibility."
            ),
        )).score
        assert good_score > short_score

    def test_evidence_includes_word_count(
        self, technical_answer_good: AnswerInput
    ) -> None:
        """Evidence must include word count."""
        from ai_core.evaluation_pipeline.communication_evaluator import CommunicationEvaluator
        evaluator = CommunicationEvaluator()
        result = evaluator.evaluate(technical_answer_good)
        word_count_evidence = [e for e in result.evidence if "word" in e.lower()]
        assert len(word_count_evidence) >= 1

    def test_dimension_name(self) -> None:
        """Dimension name must be 'communication'."""
        from ai_core.evaluation_pipeline.communication_evaluator import CommunicationEvaluator
        assert CommunicationEvaluator().dimension_name == "communication"

    def test_score_range(self, technical_answer_good: AnswerInput) -> None:
        """Score must be between 0 and 100."""
        from ai_core.evaluation_pipeline.communication_evaluator import CommunicationEvaluator
        result = CommunicationEvaluator().evaluate(technical_answer_good)
        assert 0.0 <= result.score <= 100.0


# ---------------------------------------------------------------------------
# EvidenceEvaluator tests
# ---------------------------------------------------------------------------

class TestEvidenceEvaluator:
    """Tests for EvidenceEvaluator."""

    def test_answer_with_example_scores_higher(self) -> None:
        """Answer with 'for example' should score above answer without it."""
        from ai_core.evaluation_pipeline.evidence_evaluator import EvidenceEvaluator
        evaluator = EvidenceEvaluator()

        base = AnswerInput(
            session_id=1, user_id=1, question_id="q1", competency_id="c1",
            question_text="Explain X.", question_type=QuestionType.TECHNICAL,
            sample_answer="X is Y.", required_concepts=[], optional_concepts=[],
            rubric_id="r1", user_answer="X is Y because of Z.",
        )
        with_example = AnswerInput(
            session_id=1, user_id=1, question_id="q1", competency_id="c1",
            question_text="Explain X.", question_type=QuestionType.TECHNICAL,
            sample_answer="X is Y.", required_concepts=[], optional_concepts=[],
            rubric_id="r1",
            user_answer=(
                "X is Y because of Z. For example, in my project I used "
                "Python and FastAPI to implement this pattern in production."
            ),
        )
        base_score = evaluator.evaluate(base).score
        example_score = evaluator.evaluate(with_example).score
        assert example_score > base_score

    def test_technology_signals_detected(self) -> None:
        """Technology names in answer should boost evidence score."""
        from ai_core.evaluation_pipeline.evidence_evaluator import EvidenceEvaluator
        evaluator = EvidenceEvaluator()
        answer = AnswerInput(
            session_id=1, user_id=1, question_id="q1", competency_id="c1",
            question_text="Q?", question_type=QuestionType.TECHNICAL,
            sample_answer="Sample.", required_concepts=[], optional_concepts=[],
            rubric_id="r1",
            user_answer="I used Python, FastAPI, and PostgreSQL in production.",
        )
        result = evaluator.evaluate(answer)
        tech_evidence = [e for e in result.evidence if "Technology" in e]
        assert len(tech_evidence) >= 1

    def test_no_evidence_answer_scores_zero_to_low(self) -> None:
        """Generic answer with no signals should score low (0-35)."""
        from ai_core.evaluation_pipeline.evidence_evaluator import EvidenceEvaluator
        evaluator = EvidenceEvaluator()
        answer = AnswerInput(
            session_id=1, user_id=1, question_id="q1", competency_id="c1",
            question_text="Q?", question_type=QuestionType.TECHNICAL,
            sample_answer="Sample.", required_concepts=[], optional_concepts=[],
            rubric_id="r1",
            user_answer="This concept is important and useful in programming.",
        )
        result = evaluator.evaluate(answer)
        assert result.score <= 35.0

    def test_dimension_name(self) -> None:
        """Dimension name must be 'evidence'."""
        from ai_core.evaluation_pipeline.evidence_evaluator import EvidenceEvaluator
        assert EvidenceEvaluator().dimension_name == "evidence"


# ---------------------------------------------------------------------------
# ReasoningEvaluator tests
# ---------------------------------------------------------------------------

class TestReasoningEvaluator:
    """Tests for ReasoningEvaluator."""

    def test_causal_language_boosts_score(self) -> None:
        """Answer with causal connectors should score higher than bare answer."""
        from ai_core.evaluation_pipeline.reasoning_evaluator import ReasoningEvaluator
        evaluator = ReasoningEvaluator()

        bare = AnswerInput(
            session_id=1, user_id=1, question_id="q1", competency_id="c1",
            question_text="Q?", question_type=QuestionType.TECHNICAL,
            sample_answer="Sample.", required_concepts=[], optional_concepts=[],
            rubric_id="r1",
            user_answer="Encapsulation bundles data. Inheritance reuses code.",
        )
        causal = AnswerInput(
            session_id=1, user_id=1, question_id="q1", competency_id="c1",
            question_text="Q?", question_type=QuestionType.TECHNICAL,
            sample_answer="Sample.", required_concepts=[], optional_concepts=[],
            rubric_id="r1",
            user_answer=(
                "Encapsulation bundles data because it prevents external "
                "access to internal state, therefore reducing bugs. "
                "Inheritance is useful because it enables code reuse, "
                "which means less duplication and easier maintenance. "
                "Polymorphism is powerful compared to type-checking because "
                "it allows extensibility without modifying existing code."
            ),
        )
        bare_score = evaluator.evaluate(bare).score
        causal_score = evaluator.evaluate(causal).score
        assert causal_score > bare_score

    def test_dimension_name(self) -> None:
        """Dimension name must be 'reasoning'."""
        from ai_core.evaluation_pipeline.reasoning_evaluator import ReasoningEvaluator
        assert ReasoningEvaluator().dimension_name == "reasoning"

    def test_score_range(self, technical_answer_good: AnswerInput) -> None:
        """Score must be between 0 and 100."""
        from ai_core.evaluation_pipeline.reasoning_evaluator import ReasoningEvaluator
        result = ReasoningEvaluator().evaluate(technical_answer_good)
        assert 0.0 <= result.score <= 100.0

    def test_evidence_not_empty(self, technical_answer_good: AnswerInput) -> None:
        """Evidence list must not be empty."""
        from ai_core.evaluation_pipeline.reasoning_evaluator import ReasoningEvaluator
        result = ReasoningEvaluator().evaluate(technical_answer_good)
        assert len(result.evidence) >= 1


# ---------------------------------------------------------------------------
# ScoreFusion tests
# ---------------------------------------------------------------------------

class TestScoreFusion:
    """Tests for ScoreFusion."""

    def _make_dim(self, score: float, label: str) -> object:
        """Create a stub DimensionScore."""
        from ai_core.evaluation_pipeline.base_evaluator import DimensionScore
        return DimensionScore(score=score, label=label, reason="test", evidence=[])

    def test_weighted_final_within_range(self) -> None:
        """Weighted final must be 0-100."""
        from ai_core.evaluation_pipeline.score_fusion import FusionInput, ScoreFusion
        fusion = ScoreFusion()
        fi = FusionInput(
            semantic=self._make_dim(80.0, "Semantic"),
            concept=self._make_dim(70.0, "Concept"),
            communication=self._make_dim(75.0, "Communication"),
            evidence=self._make_dim(60.0, "Evidence"),
            reasoning=self._make_dim(65.0, "Reasoning"),
            question_type=QuestionType.TECHNICAL,
        )
        scores = fusion.fuse(fi)
        assert 0.0 <= scores.weighted_final <= 100.0

    def test_technical_vs_hr_weights_differ(self) -> None:
        """Technical and HR weight profiles must produce different results."""
        from ai_core.evaluation_pipeline.score_fusion import FusionInput, ScoreFusion
        fusion = ScoreFusion()
        dims = dict(
            semantic=self._make_dim(90.0, "Semantic"),
            concept=self._make_dim(40.0, "Concept"),
            communication=self._make_dim(90.0, "Communication"),
            evidence=self._make_dim(90.0, "Evidence"),
            reasoning=self._make_dim(40.0, "Reasoning"),
        )
        tech_scores = fusion.fuse(FusionInput(**dims, question_type=QuestionType.TECHNICAL))
        hr_scores = fusion.fuse(FusionInput(**dims, question_type=QuestionType.HR))
        # Concept is weighted higher for technical, so tech should score lower here
        assert tech_scores.weighted_final != hr_scores.weighted_final

    def test_grade_a_for_high_score(self) -> None:
        """Score >= 90 must give grade A."""
        from ai_core.evaluation_pipeline.score_fusion import ScoreFusion
        fusion = ScoreFusion()
        assert fusion.get_grade(95.0) == GradeEnum.A

    def test_grade_f_for_low_score(self) -> None:
        """Score < 40 must give grade F."""
        from ai_core.evaluation_pipeline.score_fusion import ScoreFusion
        fusion = ScoreFusion()
        assert fusion.get_grade(20.0) == GradeEnum.F

    def test_readiness_excellent_for_high_score(self) -> None:
        """Score >= 85 must give excellent readiness."""
        from ai_core.evaluation_pipeline.score_fusion import ScoreFusion
        fusion = ScoreFusion()
        assert fusion.get_readiness(90.0) == ReadinessEnum.EXCELLENT

    def test_readiness_poor_for_low_score(self) -> None:
        """Score < 50 must give poor readiness."""
        from ai_core.evaluation_pipeline.score_fusion import ScoreFusion
        fusion = ScoreFusion()
        assert fusion.get_readiness(30.0) == ReadinessEnum.POOR

    def test_all_scores_present_in_output(self) -> None:
        """EvaluationScores must contain all 6 fields."""
        from ai_core.evaluation_pipeline.score_fusion import FusionInput, ScoreFusion
        fusion = ScoreFusion()
        fi = FusionInput(
            semantic=self._make_dim(75.0, "Semantic"),
            concept=self._make_dim(75.0, "Concept"),
            communication=self._make_dim(75.0, "Communication"),
            evidence=self._make_dim(75.0, "Evidence"),
            reasoning=self._make_dim(75.0, "Reasoning"),
            question_type=QuestionType.TECHNICAL,
        )
        scores = fusion.fuse(fi)
        assert scores.semantic == 75.0
        assert scores.concept == 75.0
        assert scores.communication == 75.0
        assert scores.evidence == 75.0
        assert scores.reasoning == 75.0
        assert scores.weighted_final > 0


# ---------------------------------------------------------------------------
# ExplainabilityEngine tests
# ---------------------------------------------------------------------------

class TestExplainabilityEngine:
    """Tests for ExplainabilityEngine."""

    def _make_dim(self, score: float, label: str, reason: str = "test reason",
                   evidence: list[str] | None = None) -> object:
        """Create a stub DimensionScore."""
        from ai_core.evaluation_pipeline.base_evaluator import DimensionScore
        return DimensionScore(score=score, label=label, reason=reason,
                              evidence=evidence or [])

    def test_explanation_has_all_reasons(self) -> None:
        """EvaluationExplanation must have all 7 required fields populated."""
        from ai_core.evaluation_pipeline.explainability import ExplainabilityEngine
        from ai_core.evaluation_pipeline.score_fusion import FusionInput
        engine = ExplainabilityEngine()
        fi = FusionInput(
            semantic=self._make_dim(70.0, "Semantic", "Good semantic match"),
            concept=self._make_dim(80.0, "Concept", "All concepts found"),
            communication=self._make_dim(65.0, "Communication", "Clear structure"),
            evidence=self._make_dim(55.0, "Evidence", "Some examples given"),
            reasoning=self._make_dim(60.0, "Reasoning", "Causal reasoning used"),
            question_type=QuestionType.TECHNICAL,
        )
        explanation = engine.build_explanation(
            fusion_input=fi,
            grade=GradeEnum.B,
            readiness=ReadinessEnum.GOOD,
            weighted_final=74.0,
        )
        assert explanation.semantic_reason == "Good semantic match"
        assert explanation.concept_reason == "All concepts found"
        assert explanation.communication_reason == "Clear structure"
        assert explanation.evidence_reason == "Some examples given"
        assert explanation.reasoning_reason == "Causal reasoning used"
        assert len(explanation.overall_summary) > 20
        assert len(explanation.improvement_tip) > 20

    def test_evidence_matched_concepts_parsed(self) -> None:
        """Matched concepts should be extracted from concept dimension evidence."""
        from ai_core.evaluation_pipeline.explainability import ExplainabilityEngine
        engine = ExplainabilityEngine()
        concept_dim = self._make_dim(
            80.0, "Concept", "Good",
            evidence=["Required concepts found (3/4): encapsulation, inheritance, polymorphism"]
        )
        ev = engine.build_evidence(
            concept_dim=concept_dim,
            communication_dim=self._make_dim(70.0, "Comm", "OK"),
            evidence_dim=self._make_dim(60.0, "Evidence", "Some"),
            reasoning_dim=self._make_dim(60.0, "Reasoning", "Good"),
            semantic_dim=self._make_dim(75.0, "Semantic", "High"),
        )
        assert "encapsulation" in ev.matched_concepts

    def test_strengths_populated_for_high_scores(self) -> None:
        """Dimensions with score >= 70 must appear in strengths."""
        from ai_core.evaluation_pipeline.explainability import ExplainabilityEngine
        engine = ExplainabilityEngine()
        ev = engine.build_evidence(
            concept_dim=self._make_dim(85.0, "Concept", "High"),
            communication_dim=self._make_dim(80.0, "Comm", "High"),
            evidence_dim=self._make_dim(75.0, "Evidence", "High"),
            reasoning_dim=self._make_dim(70.0, "Reasoning", "High"),
            semantic_dim=self._make_dim(90.0, "Semantic", "High"),
        )
        assert len(ev.strengths) >= 3

    def test_weaknesses_populated_for_low_scores(self) -> None:
        """Dimensions with score < 50 must appear in weaknesses."""
        from ai_core.evaluation_pipeline.explainability import ExplainabilityEngine
        engine = ExplainabilityEngine()
        ev = engine.build_evidence(
            concept_dim=self._make_dim(20.0, "Concept", "Low"),
            communication_dim=self._make_dim(30.0, "Comm", "Low"),
            evidence_dim=self._make_dim(10.0, "Evidence", "Low"),
            reasoning_dim=self._make_dim(40.0, "Reasoning", "Low"),
            semantic_dim=self._make_dim(25.0, "Semantic", "Low"),
        )
        assert len(ev.weaknesses) >= 3


# ---------------------------------------------------------------------------
# EvaluationOrchestrator end-to-end tests
# ---------------------------------------------------------------------------

class TestEvaluationOrchestrator:
    """End-to-end tests for EvaluationOrchestrator."""

    def test_evaluate_returns_evaluation_output(
        self, technical_answer_good: AnswerInput
    ) -> None:
        """orchestrator.evaluate() must return a valid EvaluationOutput."""
        from ai_core.evaluation_pipeline.evaluation_orchestrator import EvaluationOrchestrator
        from schemas.evaluation_schema import EvaluationOutput
        orchestrator = EvaluationOrchestrator()
        result = orchestrator.evaluate(technical_answer_good)
        assert isinstance(result, EvaluationOutput)

    def test_evaluate_has_valid_grade(
        self, technical_answer_good: AnswerInput
    ) -> None:
        """Grade must be one of A, B, C, D, F."""
        from ai_core.evaluation_pipeline.evaluation_orchestrator import EvaluationOrchestrator
        result = EvaluationOrchestrator().evaluate(technical_answer_good)
        assert result.grade in list(GradeEnum)

    def test_evaluate_has_valid_readiness(
        self, technical_answer_good: AnswerInput
    ) -> None:
        """Readiness must be one of excellent, good, average, poor."""
        from ai_core.evaluation_pipeline.evaluation_orchestrator import EvaluationOrchestrator
        result = EvaluationOrchestrator().evaluate(technical_answer_good)
        assert result.readiness_level in list(ReadinessEnum)

    def test_good_answer_scores_higher_than_poor(
        self,
        technical_answer_good: AnswerInput,
        technical_answer_poor: AnswerInput,
    ) -> None:
        """Good answer must produce higher weighted_final than poor answer."""
        from ai_core.evaluation_pipeline.evaluation_orchestrator import EvaluationOrchestrator
        orchestrator = EvaluationOrchestrator()
        good_result = orchestrator.evaluate(technical_answer_good)
        poor_result = orchestrator.evaluate(technical_answer_poor)
        assert good_result.scores.weighted_final > poor_result.scores.weighted_final

    def test_evaluate_has_explanation_fields(
        self, technical_answer_good: AnswerInput
    ) -> None:
        """EvaluationOutput must contain all explanation fields."""
        from ai_core.evaluation_pipeline.evaluation_orchestrator import EvaluationOrchestrator
        result = EvaluationOrchestrator().evaluate(technical_answer_good)
        assert result.explanation.semantic_reason
        assert result.explanation.concept_reason
        assert result.explanation.communication_reason
        assert result.explanation.evidence_reason
        assert result.explanation.reasoning_reason
        assert result.explanation.overall_summary
        assert result.explanation.improvement_tip

    def test_evaluate_has_competency_delta(
        self, technical_answer_good: AnswerInput
    ) -> None:
        """Competency delta must be a float in reasonable range."""
        from ai_core.evaluation_pipeline.evaluation_orchestrator import EvaluationOrchestrator
        result = EvaluationOrchestrator().evaluate(technical_answer_good)
        assert isinstance(result.competency_delta, float)
        assert -0.5 <= result.competency_delta <= 0.5

    def test_evaluate_hr_answer(self, hr_answer_good: AnswerInput) -> None:
        """HR answer should evaluate without errors and return valid output."""
        from ai_core.evaluation_pipeline.evaluation_orchestrator import EvaluationOrchestrator
        from schemas.evaluation_schema import EvaluationOutput
        result = EvaluationOrchestrator().evaluate(hr_answer_good)
        assert isinstance(result, EvaluationOutput)
        assert 0.0 <= result.scores.weighted_final <= 100.0

    def test_evaluation_id_unique(
        self, technical_answer_good: AnswerInput
    ) -> None:
        """Each evaluation must have a unique UUID id."""
        from ai_core.evaluation_pipeline.evaluation_orchestrator import EvaluationOrchestrator
        orchestrator = EvaluationOrchestrator()
        result1 = orchestrator.evaluate(technical_answer_good)
        result2 = orchestrator.evaluate(technical_answer_good)
        assert result1.id != result2.id

    def test_poor_answer_gets_low_grade(
        self, technical_answer_poor: AnswerInput
    ) -> None:
        """A very poor answer should get a D or F grade."""
        from ai_core.evaluation_pipeline.evaluation_orchestrator import EvaluationOrchestrator
        result = EvaluationOrchestrator().evaluate(technical_answer_poor)
        assert result.grade in (GradeEnum.D, GradeEnum.F)

    def test_scores_all_in_valid_range(
        self, technical_answer_good: AnswerInput
    ) -> None:
        """All 6 score fields must be between 0 and 100."""
        from ai_core.evaluation_pipeline.evaluation_orchestrator import EvaluationOrchestrator
        result = EvaluationOrchestrator().evaluate(technical_answer_good)
        scores = result.scores
        for dim in [scores.semantic, scores.concept, scores.communication,
                    scores.evidence, scores.reasoning, scores.weighted_final]:
            assert 0.0 <= dim <= 100.0
