"""
Skill pipeline package.

Manages competency confidence tracking, adaptive difficulty
estimation, and skill gap identification.

Components:
    CompetencyGraph:    Knowledge graph of competencies and relationships.
    ConfidenceUpdater:  Updates competency confidence after evaluation.
    EloEstimator:       Adaptive difficulty using Elo-style rating.
    SkillGapAnalyzer:   Identifies priority skill gaps for a user.
"""

from ai_core.skill_pipeline.competency_graph import CompetencyGraph
from ai_core.skill_pipeline.confidence_updater import ConfidenceUpdater
from ai_core.skill_pipeline.elo_estimator import EloEstimator
from ai_core.skill_pipeline.skill_gap_analyzer import SkillGapAnalyzer

__all__ = [
    "CompetencyGraph",
    "ConfidenceUpdater",
    "EloEstimator",
    "SkillGapAnalyzer",
]
