"""
Tests for the recommendation pipeline.
"""

from __future__ import annotations

import pytest

from ai_core.recommendation_pipeline import (
    ResourceMatcher,
    RoadmapGenerator,
    PracticeGenerator,
    Recommender,
)
from schemas.competency_schema import CompetencyGap, PriorityEnum
from schemas.recommendation_schema import LearningRoadmap, Resource


# ─── Fixtures ────────────────────────────────────────────────

def make_gap(
    comp_id: str = "comp_se_oop",
    name: str = "Object Oriented Programming",
    confidence: float = 0.2,
    gap: float = 0.5,
    priority: PriorityEnum = PriorityEnum.HIGH,
    relevance: float = 0.9,
) -> CompetencyGap:
    """Create a CompetencyGap for testing."""
    return CompetencyGap(
        competency_id=comp_id,
        competency_name=name,
        current_confidence=confidence,
        required_confidence=0.7,
        gap=gap,
        priority=priority,
        role_relevance=relevance,
        recommended_action=f"Study {name} fundamentals.",
    )


# ─── ResourceMatcher Tests ────────────────────────────────────

class TestResourceMatcher:
    """Tests for ResourceMatcher."""

    def test_matcher_loads_resources(self) -> None:
        """ResourceMatcher loads resources on init."""
        matcher = ResourceMatcher()
        assert matcher.resource_count() > 0

    def test_match_for_gap_returns_resources(self) -> None:
        """match_for_gap() returns resources for known competency."""
        matcher = ResourceMatcher()
        gap = make_gap("comp_se_oop", "Object Oriented Programming")
        resources = matcher.match_for_gap(gap, top_n=3)

        assert isinstance(resources, list)
        assert len(resources) <= 3

    def test_match_respects_top_n(self) -> None:
        """match_for_gap() respects the top_n limit."""
        matcher = ResourceMatcher()
        gap = make_gap("comp_se_oop", "Object Oriented Programming")
        resources = matcher.match_for_gap(gap, top_n=1)
        assert len(resources) <= 1

    def test_match_for_known_competency(self) -> None:
        """match_for_competency_id() returns resources."""
        matcher = ResourceMatcher()
        resources = matcher.match_for_competency_id("comp_se_oop")
        assert isinstance(resources, list)

    def test_match_returns_resource_objects(self) -> None:
        """Returned items are Resource instances."""
        matcher = ResourceMatcher()
        gap = make_gap("comp_se_oop", "Object Oriented Programming")
        resources = matcher.match_for_gap(gap)

        for resource in resources:
            assert isinstance(resource, Resource)
            assert resource.id != ""
            assert resource.url != ""

    def test_get_all_resources(self) -> None:
        """get_all_resources() returns complete list."""
        matcher = ResourceMatcher()
        all_res = matcher.get_all_resources()
        assert len(all_res) == matcher.resource_count()

    def test_fallback_for_unknown_competency(self) -> None:
        """match_for_gap() returns fallback for unknown competency."""
        matcher = ResourceMatcher()
        gap = make_gap("comp_unknown_xyz", "Unknown Topic")
        resources = matcher.match_for_gap(gap, top_n=2)
        # Should not raise, may return empty or fallback
        assert isinstance(resources, list)

    def test_difficulty_alignment_beginner_user(self) -> None:
        """Low confidence user gets beginner-friendly resources first."""
        matcher = ResourceMatcher()
        gap = make_gap("comp_se_oop", "Object Oriented Programming", confidence=0.05)
        resources = matcher.match_for_gap(gap, top_n=3)

        if resources:
            first = resources[0]
            assert first.difficulty in ["beginner", "intermediate"]


# ─── RoadmapGenerator Tests ──────────────────────────────────

class TestRoadmapGenerator:
    """Tests for RoadmapGenerator."""

    def test_generator_initializes(self) -> None:
        """RoadmapGenerator initializes without error."""
        generator = RoadmapGenerator()
        assert generator is not None

    def test_generate_returns_roadmap(self) -> None:
        """generate() returns a LearningRoadmap."""
        generator = RoadmapGenerator()
        gaps = [
            make_gap("comp_se_oop", "Object Oriented Programming", gap=0.5),
            make_gap("comp_se_databases", "Databases", gap=0.4),
        ]

        roadmap = generator.generate(
            user_id=1,
            session_id=1,
            gaps=gaps,
            target_role="Software Engineer",
        )

        assert isinstance(roadmap, LearningRoadmap)
        assert roadmap.user_id == 1
        assert roadmap.total_weeks > 0

    def test_empty_gaps_returns_empty_roadmap(self) -> None:
        """Empty gaps produces empty roadmap."""
        generator = RoadmapGenerator()
        roadmap = generator.generate(
            user_id=1,
            session_id=1,
            gaps=[],
            target_role="Software Engineer",
        )

        assert roadmap.total_weeks == 0
        assert len(roadmap.weekly_plans) == 0

    def test_weekly_plans_have_goals(self) -> None:
        """Each weekly plan has a goal statement."""
        generator = RoadmapGenerator()
        gaps = [make_gap("comp_se_oop", "Object Oriented Programming", gap=0.5)]

        roadmap = generator.generate(
            user_id=1,
            session_id=1,
            gaps=gaps,
            target_role="Software Engineer",
        )

        for plan in roadmap.weekly_plans:
            assert isinstance(plan.goal, str)
            assert len(plan.goal) > 10

    def test_weekly_plans_have_recommendations(self) -> None:
        """Each weekly plan has recommendations."""
        generator = RoadmapGenerator()
        gaps = [make_gap("comp_se_oop", "Object Oriented Programming", gap=0.5)]

        roadmap = generator.generate(
            user_id=1,
            session_id=1,
            gaps=gaps,
            target_role="Software Engineer",
        )

        for plan in roadmap.weekly_plans:
            assert len(plan.recommendations) > 0

    def test_max_weeks_respected(self) -> None:
        """Roadmap does not exceed max_weeks."""
        generator = RoadmapGenerator()
        gaps = [make_gap(f"comp_{i}", f"Topic {i}", gap=0.5) for i in range(20)]

        roadmap = generator.generate(
            user_id=1,
            session_id=1,
            gaps=gaps,
            target_role="Software Engineer",
            max_weeks=4,
        )

        assert roadmap.total_weeks <= 4

    def test_estimated_readiness_date_set(self) -> None:
        """Roadmap includes an estimated readiness date."""
        generator = RoadmapGenerator()
        gaps = [make_gap("comp_se_oop", "Object Oriented Programming", gap=0.5)]

        roadmap = generator.generate(
            user_id=1,
            session_id=1,
            gaps=gaps,
            target_role="Software Engineer",
        )

        assert roadmap.estimated_readiness_date is not None
        assert len(roadmap.estimated_readiness_date) > 5

    def test_week_numbers_sequential(self) -> None:
        """Weekly plans have sequential week numbers."""
        generator = RoadmapGenerator()
        gaps = [
            make_gap("comp_se_oop", "Object Oriented Programming", gap=0.5),
            make_gap("comp_se_databases", "SQL", gap=0.4),
            make_gap("comp_se_algorithms", "Algo", gap=0.3),
        ]

        roadmap = generator.generate(
            user_id=1,
            session_id=1,
            gaps=gaps,
            target_role="Software Engineer",
        )

        for i, plan in enumerate(roadmap.weekly_plans, start=1):
            assert plan.week_number == i

    def test_recommendations_have_correct_user_id(self) -> None:
        """All recommendations carry the correct user_id."""
        generator = RoadmapGenerator()
        gaps = [make_gap("comp_se_oop", "Object Oriented Programming", gap=0.5)]

        roadmap = generator.generate(
            user_id=42,
            session_id=1,
            gaps=gaps,
            target_role="Software Engineer",
        )

        for plan in roadmap.weekly_plans:
            for rec in plan.recommendations:
                assert rec.user_id == 42


# ─── PracticeGenerator Tests ─────────────────────────────────

class TestPracticeGenerator:
    """Tests for PracticeGenerator."""

    def test_generator_loads_questions(self) -> None:
        """PracticeGenerator loads questions on init."""
        generator = PracticeGenerator()
        assert generator.question_count() > 0

    def test_get_practice_questions_returns_list(self) -> None:
        """get_practice_questions() returns a list."""
        generator = PracticeGenerator()
        gap = make_gap("comp_se_oop", "Object Oriented Programming")
        questions = generator.get_practice_questions(gap, top_n=3)

        assert isinstance(questions, list)

    def test_practice_questions_respect_top_n(self) -> None:
        """get_practice_questions() respects top_n."""
        generator = PracticeGenerator()
        gap = make_gap("comp_se_oop", "Object Oriented Programming")
        questions = generator.get_practice_questions(gap, top_n=1)

        assert len(questions) <= 1

    def test_exclude_ids_works(self) -> None:
        """Already asked questions are excluded."""
        generator = PracticeGenerator()
        gap = make_gap("comp_se_oop", "Object Oriented Programming")

        all_questions = generator.get_practice_questions(gap, top_n=10)
        if not all_questions:
            return

        first_id = all_questions[0].id
        remaining = generator.get_practice_questions(
            gap, top_n=10, exclude_ids=[first_id]
        )

        ids = [q.id for q in remaining]
        assert first_id not in ids

    def test_get_practice_for_multiple_gaps(self) -> None:
        """get_practice_for_multiple_gaps() returns dict."""
        generator = PracticeGenerator()
        gaps = [
            make_gap("comp_se_oop", "Object Oriented Programming"),
            make_gap("comp_se_databases", "SQL"),
        ]

        result = generator.get_practice_for_multiple_gaps(gaps)
        assert isinstance(result, dict)

    def test_follow_up_hints_returned(self) -> None:
        """get_follow_up_hints() returns hints list."""
        generator = PracticeGenerator()
        gap = make_gap("comp_se_oop", "Object Oriented Programming")
        questions = generator.get_practice_questions(gap)

        if questions:
            hints = generator.get_follow_up_hints(questions[0])
            assert isinstance(hints, list)

    def test_competency_count(self) -> None:
        """competency_count() returns non-zero."""
        generator = PracticeGenerator()
        assert generator.competency_count() > 0


# ─── Recommender Tests ────────────────────────────────────────

class TestRecommender:
    """Tests for the full Recommender orchestrator."""

    def test_recommender_initializes(self) -> None:
        """Recommender initializes without error."""
        recommender = Recommender()
        assert recommender is not None

    def test_recommend_returns_output(self) -> None:
        """recommend() returns RecommendationOutput."""
        from ai_core.recommendation_pipeline.recommender import RecommendationOutput

        recommender = Recommender()
        gaps = [
            make_gap("comp_se_oop", "Object Oriented Programming", gap=0.5),
            make_gap("comp_se_databases", "SQL", gap=0.4),
        ]

        output = recommender.recommend(
            user_id=1,
            session_id=1,
            gaps=gaps,
            target_role="Software Engineer",
        )

        assert isinstance(output, RecommendationOutput)
        assert isinstance(output.roadmap, LearningRoadmap)

    def test_recommend_with_no_gaps(self) -> None:
        """recommend() handles empty gaps gracefully."""
        recommender = Recommender()
        output = recommender.recommend(
            user_id=1,
            session_id=1,
            gaps=[],
            target_role="Software Engineer",
        )

        assert output.roadmap.total_weeks == 0
        assert output.top_resources == []

    def test_recommend_top_resources_unique(self) -> None:
        """Top resources contain no duplicates."""
        recommender = Recommender()
        gaps = [
            make_gap("comp_se_oop", "Object Oriented Programming", gap=0.5),
            make_gap("comp_se_databases", "SQL", gap=0.4),
            make_gap("comp_se_algorithms", "Algo", gap=0.3),
        ]

        output = recommender.recommend(
            user_id=1,
            session_id=1,
            gaps=gaps,
            target_role="Software Engineer",
        )

        resource_ids = [r.id for r in output.top_resources]
        assert len(resource_ids) == len(set(resource_ids))

    def test_recommend_next_steps(self) -> None:
        """recommend_next_steps() returns immediate recommendations."""
        recommender = Recommender()
        gaps = [
            make_gap("comp_se_oop", "Object Oriented Programming", gap=0.5),
            make_gap("comp_se_databases", "SQL", gap=0.4),
        ]

        recs = recommender.recommend_next_steps(
            user_id=1,
            session_id=1,
            gaps=gaps,
            top_n=2,
        )

        assert len(recs) <= 2
        for rec in recs:
            assert rec.user_id == 1
            assert rec.competency_id != ""

    def test_recommend_next_steps_empty_gaps(self) -> None:
        """recommend_next_steps() handles empty gaps."""
        recommender = Recommender()
        recs = recommender.recommend_next_steps(
            user_id=1,
            session_id=1,
            gaps=[],
        )
        assert recs == []

    def test_practice_questions_in_output(self) -> None:
        """Output includes practice questions for weak competencies."""
        recommender = Recommender()
        gaps = [
            make_gap("comp_se_oop", "Object Oriented Programming", confidence=0.1, gap=0.6),
        ]

        output = recommender.recommend(
            user_id=1,
            session_id=1,
            gaps=gaps,
            target_role="Software Engineer",
        )

        # practice_questions is dict competency_id -> questions
        assert isinstance(output.practice_questions, dict)

    def test_critical_recommendations_are_high_priority(self) -> None:
        """Critical recommendations are all high priority."""
        recommender = Recommender()
        gaps = [
            make_gap("comp_se_oop", "Object Oriented Programming", priority=PriorityEnum.HIGH),
            make_gap("comp_se_databases", "SQL", priority=PriorityEnum.MEDIUM),
        ]

        output = recommender.recommend(
            user_id=1,
            session_id=1,
            gaps=gaps,
            target_role="Software Engineer",
        )

        for critical_rec in output.critical_recommendations:
            assert critical_rec.priority == PriorityEnum.HIGH.value
