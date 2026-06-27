"""
Resource matcher.

Matches identified skill gaps to relevant learning resources
using content-based filtering and competency mapping.

Resources are loaded from data/resources/learning_resources.json.
Matching is done by competency_id overlap and difficulty alignment.
"""

from __future__ import annotations

import json
from pathlib import Path

from ai_core.shared.similarity import SimilarityCalculator
from schemas.competency_schema import CompetencyGap
from schemas.recommendation_schema import Resource, ResourceType


class ResourceMatcher:
    """
    Matches competency gaps to relevant learning resources.

    Uses content-based filtering:
    1. Filter resources by competency_id overlap.
    2. Rank by difficulty alignment with current gap.
    3. Return top-N resources per competency.
    """

    def __init__(self) -> None:
        """Load resources from JSON data file."""
        self._resources: list[Resource] = []
        self._resources_by_competency: dict[str, list[Resource]] = {}
        self._load_resources()

    def _load_resources(self) -> None:
        """
        Load learning resources from JSON file.

        Raises:
            FileNotFoundError: If resources file not found.
        """
        resources_path = (
            Path(__file__).parent.parent.parent
            / "data"
            / "resources"
            / "learning_resources.json"
        )

        if not resources_path.exists():
            raise FileNotFoundError(
                f"Resources file not found: {resources_path}"
            )

        with open(resources_path, "r") as f:
            raw_data = json.load(f)

        for res_data in raw_data.get("resources", []):
            resource = Resource(
                id=res_data["id"],
                title=res_data["title"],
                url=res_data["url"],
                resource_type=ResourceType(res_data["resource_type"]),
                difficulty=res_data.get("difficulty", "intermediate"),
                competency_ids=res_data.get("competency_ids", []),
                description=res_data.get("description", ""),
            )
            self._resources.append(resource)

            # Index by competency
            for comp_id in resource.competency_ids:
                if comp_id not in self._resources_by_competency:
                    self._resources_by_competency[comp_id] = []
                self._resources_by_competency[comp_id].append(resource)

        print(f"Loaded {len(self._resources)} learning resources")

    def match_for_gap(
        self,
        gap: CompetencyGap,
        top_n: int = 3,
    ) -> list[Resource]:
        """
        Find the most relevant resources for a competency gap.

        Args:
            gap: The identified competency gap.
            top_n: Maximum number of resources to return.

        Returns:
            List of matched Resources sorted by relevance.
        """
        # Get resources directly indexed to this competency
        direct_matches = self._resources_by_competency.get(
            gap.competency_id, []
        )

        if not direct_matches:
            # Fall back to description-based matching
            return self._fallback_match(gap, top_n)

        # Rank by difficulty alignment
        ranked = self._rank_by_difficulty(
            resources=direct_matches,
            current_confidence=gap.current_confidence,
        )

        return ranked[:top_n]

    def match_for_competency_id(
        self,
        competency_id: str,
        top_n: int = 2,
    ) -> list[Resource]:
        """
        Find resources for a specific competency ID.

        Args:
            competency_id: Competency to find resources for.
            top_n: Maximum resources to return.

        Returns:
            List of matched Resources.
        """
        matches = self._resources_by_competency.get(competency_id, [])
        return matches[:top_n]

    def _rank_by_difficulty(
        self,
        resources: list[Resource],
        current_confidence: float,
    ) -> list[Resource]:
        """
        Rank resources by difficulty alignment with user level.

        A user with low confidence should get beginner resources first.
        A user with high confidence should get intermediate/advanced.

        Args:
            resources: Candidate resources.
            current_confidence: User's current confidence 0.0-1.0.

        Returns:
            Resources sorted by difficulty alignment.
        """
        def difficulty_score(resource: Resource) -> float:
            """Compute how well resource difficulty matches user level."""
            difficulty_map = {
                "beginner": 0.2,
                "intermediate": 0.5,
                "advanced": 0.8,
            }
            resource_level = difficulty_map.get(
                resource.difficulty.lower(), 0.5
            )

            # Prefer resources slightly above current confidence
            # (challenge without overwhelming)
            target_level = min(current_confidence + 0.15, 0.8)
            distance = abs(resource_level - target_level)
            return 1.0 - distance

        return sorted(resources, key=difficulty_score, reverse=True)

    def _fallback_match(
        self,
        gap: CompetencyGap,
        top_n: int,
    ) -> list[Resource]:
        """
        Fallback matching using competency name similarity.

        Used when no resources are directly indexed to the competency.

        Args:
            gap: The competency gap.
            top_n: Maximum resources to return.

        Returns:
            Best matching resources using description similarity.
        """
        if not self._resources:
            return []

        # Score each resource by name similarity to competency
        scored = []
        for resource in self._resources:
            score = SimilarityCalculator.jaccard_similarity(
                gap.competency_name.lower(),
                (resource.title + " " + resource.description).lower(),
            )
            scored.append((resource, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [r for r, _ in scored[:top_n]]

    def get_all_resources(self) -> list[Resource]:
        """Get all loaded resources."""
        return list(self._resources)

    def resource_count(self) -> int:
        """Get total number of loaded resources."""
        return len(self._resources)
