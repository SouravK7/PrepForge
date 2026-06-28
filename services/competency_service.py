"""
Competency service.

Manages competency score retrieval, gap analysis,
and skill graph generation.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from ai_core.skill_pipeline import (
    CompetencyGraph,
    SkillGapAnalyzer,
    EloEstimator,
)
from database.repositories import CompetencyScoreRepository
from schemas.competency_schema import (
    CompetencyGap,
    CompetencyScore,
    SkillGraph,
)


class CompetencyService:
    """
    Manages user competency scores and skill gap analysis.

    Provides:
    - Current skill graph for a user
    - Ranked skill gaps
    - Overall interview readiness score
    - Adaptive difficulty recommendations
    """

    def __init__(self, db_session: Session) -> None:
        """
        Initialize with database session.

        Args:
            db_session: SQLAlchemy database session.
        """
        self._db = db_session
        self._score_repo = CompetencyScoreRepository(db_session)
        self._graph = CompetencyGraph()
        self._gap_analyzer = SkillGapAnalyzer()
        self._elo = EloEstimator()

    def get_skill_graph(
        self,
        user_id: int,
        job_role: str,
    ) -> SkillGraph:
        """
        Get the skill graph for a user.

        Args:
            user_id: Target user.
            job_role: Role display name to load competencies for.

        Returns:
            SkillGraph with confidence-colored nodes.
        """
        role_id = self._role_to_id(job_role)
        self._graph.load_role(role_id)

        competency_scores = self._score_repo.to_schema_dict(user_id)

        return self._graph.build_skill_graph_schema(
            user_id=user_id,
            competency_scores=competency_scores,
        )

    def get_skill_gaps(
        self,
        user_id: int,
        job_role: str,
        top_n: int = 10,
    ) -> list[CompetencyGap]:
        """
        Get prioritized skill gaps for a user.

        Args:
            user_id: Target user.
            job_role: Target job role display name.
            top_n: Maximum gaps to return.

        Returns:
            Sorted CompetencyGap list.
        """
        role_id = self._role_to_id(job_role)
        self._graph.load_role(role_id)

        competency_scores = self._score_repo.to_schema_dict(user_id)
        competencies = self._graph.get_competencies_for_role(job_role)

        gaps = self._gap_analyzer.analyze(
            competencies=competencies,
            competency_scores=competency_scores,
            target_role=job_role,
        )

        return gaps[:top_n]

    def get_overall_readiness(
        self,
        user_id: int,
        job_role: str,
    ) -> float:
        """
        Get overall interview readiness percentage.

        Args:
            user_id: Target user.
            job_role: Target job role.

        Returns:
            Readiness percentage 0.0-100.0.
        """
        role_id = self._role_to_id(job_role)
        self._graph.load_role(role_id)

        competency_scores = self._score_repo.to_schema_dict(user_id)
        competencies = self._graph.get_competencies_for_role(job_role)

        return self._gap_analyzer.compute_overall_readiness(
            competencies=competencies,
            competency_scores=competency_scores,
            target_role=job_role,
        )

    def get_user_scores(
        self,
        user_id: int,
    ) -> dict[str, CompetencyScore]:
        """
        Get all competency scores for a user.

        Args:
            user_id: Target user.

        Returns:
            Dict of competency_id to CompetencyScore schema.
        """
        return self._score_repo.to_schema_dict(user_id)

    def get_strong_areas(
        self,
        user_id: int,
        threshold: float = 0.7,
        limit: int = 3,
    ) -> list[str]:
        """
        Get competency names where user is strong.

        Args:
            user_id: Target user.
            threshold: Minimum confidence to be strong.
            limit: Maximum to return.

        Returns:
            List of strong competency names.
        """
        scores = self._score_repo.to_schema_dict(user_id)
        strong = [
            comp_id
            for comp_id, score in scores.items()
            if score.confidence >= threshold
        ]

        results = []
        for comp_id in strong[:limit]:
            comp = self._graph.get_competency(comp_id)
            if comp:
                results.append(comp.name)
            else:
                results.append(comp_id)

        return results

    def _role_to_id(self, job_role: str) -> str:
        """
        Convert display role name to file ID.

        Args:
            job_role: Display name e.g. "Software Engineer".

        Returns:
            File ID e.g. "software_engineer".
        """
        mapping = {
            "Software Engineer": "software_engineer",
            "Data Analyst": "data_analyst",
            "AI Engineer": "ai_engineer",
        }
        return mapping.get(
            job_role,
            job_role.lower().replace(" ", "_"),
        )
