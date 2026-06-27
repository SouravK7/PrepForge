"""
Recommendation pipeline package.

Generates personalized learning recommendations based on
identified skill gaps and competency confidence scores.

Components:
    ResourceMatcher:    Matches skill gaps to learning resources.
    RoadmapGenerator:   Generates week-by-week learning roadmap.
    PracticeGenerator:  Suggests practice questions per competency.
    Recommender:        Orchestrates the full recommendation pipeline.
"""

from ai_core.recommendation_pipeline.resource_matcher import ResourceMatcher
from ai_core.recommendation_pipeline.roadmap_generator import RoadmapGenerator
from ai_core.recommendation_pipeline.practice_generator import PracticeGenerator
from ai_core.recommendation_pipeline.recommender import Recommender

__all__ = [
    "ResourceMatcher",
    "RoadmapGenerator",
    "PracticeGenerator",
    "Recommender",
]
