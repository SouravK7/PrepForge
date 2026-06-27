"""
Tests for the skill pipeline.

Tests competency graph, confidence updater, Elo estimator,
and skill gap analyzer.
"""

from __future__ import annotations

import pytest

from ai_core.skill_pipeline import (
    CompetencyGraph,
    ConfidenceUpdater,
    EloEstimator,
    SkillGapAnalyzer,
)
from schemas.competency_schema import (
    Competency,
    CompetencyScore,
    PriorityEnum,
)
from schemas.question_schema import DifficultyLevel


# ─── Fixtures ────────────────────────────────────────────────

def make_competency_score(
    user_id: int = 1,
    competency_id: str = "comp_se_oop",
    confidence: float = 0.3,
    elo: float = 1000.0,
    evidence_count: int = 0,
) -> CompetencyScore:
    """Create a CompetencyScore for testing."""
    return CompetencyScore(
        user_id=user_id,
        competency_id=competency_id,
        confidence=confidence,
        elo_rating=elo,
        evidence_count=evidence_count,
        improvement_trend=0.0,
    )


def make_competency(
    comp_id: str = "comp_se_oop",
    name: str = "OOP",
    confidence: float = 0.0,
    role: str = "Software Engineer",
    relevance: float = 0.95,
) -> Competency:
    """Create a Competency for testing."""
    return Competency(
        id=comp_id,
        name=name,
        description="Test competency",
        required_concepts=["encapsulation", "inheritance"],
        role_relevance={role: relevance},
        confidence_score=confidence,
    )


# ─── CompetencyGraph Tests ────────────────────────────────────

class TestCompetencyGraph:
    """Tests for CompetencyGraph."""

    def test_graph_initializes(self) -> None:
        """CompetencyGraph initializes without error."""
        graph = CompetencyGraph()
        assert graph is not None
        assert graph.competency_count() == 0

    def test_load_role(self) -> None:
        """load_role() loads competencies from JSON."""
        graph = CompetencyGraph()
        graph.load_role("software_engineer")
        assert graph.competency_count() > 0

    def test_load_role_twice_is_idempotent(self) -> None:
        """Loading same role twice does not duplicate competencies."""
        graph = CompetencyGraph()
        graph.load_role("software_engineer")
        count_first = graph.competency_count()
        graph.load_role("software_engineer")
        count_second = graph.competency_count()
        assert count_first == count_second

    def test_get_competency_returns_correct(self) -> None:
        """get_competency() returns the right competency."""
        graph = CompetencyGraph()
        graph.load_role("software_engineer")
        comp = graph.get_competency("comp_se_oop")
        assert comp is not None
        assert comp.name == "Object Oriented Programming"

    def test_get_competency_missing_returns_none(self) -> None:
        """get_competency() returns None for unknown id."""
        graph = CompetencyGraph()
        assert graph.get_competency("nonexistent_comp") is None

    def test_get_competencies_for_role(self) -> None:
        """get_competencies_for_role() filters by relevance."""
        graph = CompetencyGraph()
        graph.load_role("software_engineer")
        comps = graph.get_competencies_for_role("Software Engineer")
        assert len(comps) > 0
        for comp in comps:
            assert comp.role_relevance.get("Software Engineer", 0.0) >= 0.5

    def test_update_competency_score(self) -> None:
        """update_competency_score() updates graph node values."""
        graph = CompetencyGraph()
        graph.load_role("software_engineer")
        graph.update_competency_score(
            competency_id="comp_se_oop",
            new_confidence=0.75,
            new_elo=1250.0,
            evidence_count=3,
        )
        confidence = graph.get_confidence("comp_se_oop")
        assert abs(confidence - 0.75) < 0.001

    def test_get_confidence_default_zero(self) -> None:
        """get_confidence() returns 0.0 for unknown competency."""
        graph = CompetencyGraph()
        assert graph.get_confidence("unknown") == 0.0

    def test_build_skill_graph_schema(self) -> None:
        """build_skill_graph_schema() returns SkillGraph."""
        from schemas.competency_schema import SkillGraph

        graph = CompetencyGraph()
        graph.load_role("software_engineer")
        skill_graph = graph.build_skill_graph_schema(
            user_id=1,
            competency_scores={},
        )
        assert isinstance(skill_graph, SkillGraph)
        assert len(skill_graph.nodes) > 0

    def test_get_weakest_competencies(self) -> None:
        """get_weakest_competencies() returns sorted gaps."""
        graph = CompetencyGraph()
        graph.load_role("software_engineer")
        scores = {}
        weakest = graph.get_weakest_competencies(
            competency_scores=scores,
            role="Software Engineer",
            top_n=3,
        )
        assert len(weakest) <= 3
        for comp_id, gap, relevance in weakest:
            assert gap >= 0.0
            assert relevance >= 0.0

    def test_missing_role_file_raises_error(self) -> None:
        """load_role() raises FileNotFoundError for unknown role."""
        graph = CompetencyGraph()
        with pytest.raises(FileNotFoundError):
            graph.load_role("nonexistent_role")

    def test_has_competency(self) -> None:
        """has_competency() returns correct boolean."""
        graph = CompetencyGraph()
        graph.load_role("software_engineer")
        assert graph.has_competency("comp_se_oop")
        assert not graph.has_competency("nonexistent")


# ─── ConfidenceUpdater Tests ──────────────────────────────────

class TestConfidenceUpdater:
    """Tests for ConfidenceUpdater."""

    def test_updater_initializes(self) -> None:
        """ConfidenceUpdater initializes without error."""
        updater = ConfidenceUpdater()
        assert updater is not None

    def test_high_score_increases_confidence(self) -> None:
        """High evaluation score increases competency confidence."""
        updater = ConfidenceUpdater()
        score = make_competency_score(confidence=0.3)
        updated, record = updater.update(score, evaluation_score=90.0)

        assert updated.confidence > 0.3
        assert record.delta > 0

    def test_low_score_decreases_confidence(self) -> None:
        """Low evaluation score decreases competency confidence."""
        updater = ConfidenceUpdater()
        score = make_competency_score(confidence=0.6)
        updated, record = updater.update(score, evaluation_score=20.0)

        assert updated.confidence < 0.6
        assert record.delta < 0

    def test_score_stays_in_bounds(self) -> None:
        """Confidence stays between 0 and 1."""
        updater = ConfidenceUpdater()

        # Try to push above 1.0
        score = make_competency_score(confidence=0.95)
        updated, _ = updater.update(score, evaluation_score=100.0)
        assert 0.0 <= updated.confidence <= 1.0

        # Try to push below 0.0
        score = make_competency_score(confidence=0.05)
        updated, _ = updater.update(score, evaluation_score=0.0)
        assert 0.0 <= updated.confidence <= 1.0

    def test_evidence_count_increments(self) -> None:
        """Evidence count increases after each update."""
        updater = ConfidenceUpdater()
        score = make_competency_score(evidence_count=5)
        updated, _ = updater.update(score, evaluation_score=70.0)
        assert updated.evidence_count == 6

    def test_update_record_fields(self) -> None:
        """Update record contains all required fields."""
        updater = ConfidenceUpdater()
        score = make_competency_score(confidence=0.4)
        updated, record = updater.update(score, evaluation_score=80.0)

        assert record.competency_id == "comp_se_oop"
        assert record.old_confidence == 0.4
        assert record.new_confidence > 0.4
        assert isinstance(record.delta, float)
        assert isinstance(record.evidence_added, str)

    def test_create_initial_score(self) -> None:
        """create_initial_score() creates zero-confidence score."""
        updater = ConfidenceUpdater()
        score = updater.create_initial_score(
            user_id=1,
            competency_id="comp_se_oop",
        )
        assert score.confidence == 0.0
        assert score.user_id == 1
        assert score.competency_id == "comp_se_oop"

    def test_update_from_delta_positive(self) -> None:
        """update_from_delta() applies positive delta correctly."""
        updater = ConfidenceUpdater()
        score = make_competency_score(confidence=0.5)
        updated, record = updater.update_from_delta(score, 0.1)
        assert abs(updated.confidence - 0.6) < 0.001

    def test_update_from_delta_negative(self) -> None:
        """update_from_delta() applies negative delta correctly."""
        updater = ConfidenceUpdater()
        score = make_competency_score(confidence=0.5)
        updated, record = updater.update_from_delta(score, -0.1)
        assert abs(updated.confidence - 0.4) < 0.001


# ─── EloEstimator Tests ───────────────────────────────────────

class TestEloEstimator:
    """Tests for EloEstimator."""

    def test_estimator_initializes(self) -> None:
        """EloEstimator initializes without error."""
        estimator = EloEstimator()
        assert estimator is not None

    def test_expected_score_equal_elo(self) -> None:
        """Expected score is 0.5 when skill and question Elo are equal."""
        estimator = EloEstimator()
        expected = estimator.compute_expected_score(
            skill_elo=1200.0,
            question_elo=1200.0,
        )
        assert abs(expected - 0.5) < 0.001

    def test_expected_score_higher_skill(self) -> None:
        """Expected score > 0.5 when skill Elo exceeds question Elo."""
        estimator = EloEstimator()
        expected = estimator.compute_expected_score(
            skill_elo=1500.0,
            question_elo=1200.0,
        )
        assert expected > 0.5

    def test_update_elo_win(self) -> None:
        """Elo increases on good performance."""
        estimator = EloEstimator()
        score = make_competency_score(elo=1200.0)
        new_elo, delta = estimator.update_elo(
            current_score=score,
            question_elo=1200.0,
            actual_performance=0.9, # Better than expected 0.5
        )
        assert new_elo > 1200.0
        assert delta > 0.0

    def test_recommend_difficulty(self) -> None:
        """Recommend difficulty based on elo ranges."""
        estimator = EloEstimator()
        assert estimator.recommend_difficulty(800.0) == DifficultyLevel.BEGINNER
        assert estimator.recommend_difficulty(1200.0) == DifficultyLevel.INTERMEDIATE
        assert estimator.recommend_difficulty(1600.0) == DifficultyLevel.ADVANCED

# ─── SkillGapAnalyzer Tests ───────────────────────────────────

class TestSkillGapAnalyzer:
    """Tests for SkillGapAnalyzer."""

    def test_analyzer_initializes(self) -> None:
        """SkillGapAnalyzer initializes without error."""
        analyzer = SkillGapAnalyzer()
        assert analyzer is not None

    def test_analyze_no_gaps(self) -> None:
        """Returns empty when competencies exceed threshold."""
        analyzer = SkillGapAnalyzer()
        comp = make_competency()
        score = make_competency_score(confidence=0.8) # Above 0.7 threshold
        gaps = analyzer.analyze([comp], {comp.id: score}, "Software Engineer")
        assert len(gaps) == 0

    def test_analyze_with_gaps(self) -> None:
        """Returns gaps properly ordered when confidence is low."""
        analyzer = SkillGapAnalyzer()
        comp1 = make_competency(comp_id="c1", confidence=0.0, relevance=1.0)
        score1 = make_competency_score(competency_id="c1", confidence=0.1)
        
        comp2 = make_competency(comp_id="c2", confidence=0.0, relevance=0.5)
        score2 = make_competency_score(competency_id="c2", confidence=0.1)

        gaps = analyzer.analyze([comp1, comp2], {"c1": score1, "c2": score2}, "Software Engineer")
        assert len(gaps) == 2
        # c1 has higher relevance so it should be first
        assert gaps[0].competency_id == "c1"
        assert gaps[0].priority == PriorityEnum.HIGH
