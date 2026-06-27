"""
Competency knowledge graph.

Represents competencies as nodes and their dependencies
as directed edges. Tracks confidence scores per competency
per user and provides graph traversal utilities.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import networkx as nx

from ai_core.shared.config_loader import config
from schemas.competency_schema import (
    Competency,
    CompetencyScore,
    CompetencyUpdate,
    SkillGraph,
    SkillGraphEdge,
    SkillGraphNode,
)


class CompetencyGraph:
    """
    In-memory competency knowledge graph.

    Loads competency definitions from JSON data files,
    builds a directed graph of relationships, and provides
    methods to query, update, and visualize competency state.

    The graph is role-aware. Different roles weight
    competencies differently.
    """

    def __init__(self) -> None:
        """Initialize the competency graph."""
        self._graph = nx.DiGraph()
        self._competencies: dict[str, Competency] = {}
        self._data_path = (
            Path(__file__).parent.parent.parent / "data" / "competencies"
        )
        self._loaded_roles: set[str] = set()

        # Confidence thresholds from config
        self._high_threshold = config.get_float(
            "competencies", "confidence_thresholds.high", 0.7
        )
        self._medium_threshold = config.get_float(
            "competencies", "confidence_thresholds.medium", 0.4
        )

        # Colors from config
        self._color_high = config.get_str(
            "competencies", "confidence_colors.high", "#2ecc71"
        )
        self._color_medium = config.get_str(
            "competencies", "confidence_colors.medium", "#f39c12"
        )
        self._color_low = config.get_str(
            "competencies", "confidence_colors.low", "#e74c3c"
        )

    def load_role(self, role_id: str) -> None:
        """
        Load competency definitions for a job role.

        Args:
            role_id: Role identifier e.g. "software_engineer".
                     Must match a file in data/competencies/.

        Raises:
            FileNotFoundError: If competency file not found.
        """
        if role_id in self._loaded_roles:
            return

        filepath = self._data_path / f"{role_id}.json"
        if not filepath.exists():
            raise FileNotFoundError(
                f"Competency file not found: {filepath}"
            )

        with open(filepath, "r") as f:
            raw_data = json.load(f)

        for comp_data in raw_data.get("competencies", []):
            competency = Competency(
                id=comp_data["id"],
                name=comp_data["name"],
                description=comp_data.get("description", ""),
                parent_id=comp_data.get("parent_id"),
                children=comp_data.get("children", []),
                role_relevance=comp_data.get("role_relevance", {}),
                difficulty_level=comp_data.get("difficulty_level", "intermediate"),
                required_concepts=comp_data.get("required_concepts", []),
                related_resources=comp_data.get("related_resources", []),
                elo_rating=comp_data.get("elo_rating", 1000.0),
            )

            self._competencies[competency.id] = competency

            # Add node to graph
            self._graph.add_node(
                competency.id,
                name=competency.name,
                confidence=0.0,
                elo_rating=competency.elo_rating,
                evidence_count=0,
            )

            # Add edges for parent-child relationships
            if competency.parent_id:
                self._graph.add_edge(
                    competency.parent_id,
                    competency.id,
                    relationship="prerequisite",
                    strength=1.0,
                )

        self._loaded_roles.add(role_id)
        print(
            f"Loaded {len(raw_data.get('competencies', []))} "
            f"competencies for role: {role_id}"
        )

    def get_competency(self, competency_id: str) -> Optional[Competency]:
        """
        Get a competency definition by ID.

        Args:
            competency_id: Competency identifier.

        Returns:
            Competency if found, None otherwise.
        """
        return self._competencies.get(competency_id)

    def get_all_competencies(self) -> list[Competency]:
        """Get all loaded competency definitions."""
        return list(self._competencies.values())

    def get_competencies_for_role(
        self,
        role: str,
        min_relevance: float = 0.5,
    ) -> list[Competency]:
        """
        Get competencies relevant to a specific role.

        Args:
            role: Job role name e.g. "Software Engineer".
            min_relevance: Minimum relevance weight to include.

        Returns:
            Competencies sorted by relevance descending.
        """
        relevant = [
            comp for comp in self._competencies.values()
            if comp.role_relevance.get(role, 0.0) >= min_relevance
        ]

        return sorted(
            relevant,
            key=lambda c: c.role_relevance.get(role, 0.0),
            reverse=True,
        )

    def update_competency_score(
        self,
        competency_id: str,
        new_confidence: float,
        new_elo: float,
        evidence_count: int,
    ) -> None:
        """
        Update a competency node's scores in the graph.

        Args:
            competency_id: Which competency to update.
            new_confidence: Updated confidence score 0.0-1.0.
            new_elo: Updated Elo rating.
            evidence_count: Total evidence count.

        Raises:
            KeyError: If competency_id not in graph.
        """
        if competency_id not in self._graph:
            raise KeyError(f"Competency not in graph: {competency_id}")

        self._graph.nodes[competency_id]["confidence"] = new_confidence
        self._graph.nodes[competency_id]["elo_rating"] = new_elo
        self._graph.nodes[competency_id]["evidence_count"] = evidence_count

    def get_confidence(self, competency_id: str) -> float:
        """
        Get current confidence score for a competency.

        Args:
            competency_id: Competency identifier.

        Returns:
            Confidence score 0.0-1.0. Returns 0.0 if not found.
        """
        if competency_id not in self._graph:
            return 0.0
        return float(self._graph.nodes[competency_id].get("confidence", 0.0))

    def get_elo_rating(self, competency_id: str) -> float:
        """
        Get current Elo rating for a competency.

        Args:
            competency_id: Competency identifier.

        Returns:
            Elo rating. Returns default 1000.0 if not found.
        """
        if competency_id not in self._graph:
            return 1000.0
        return float(self._graph.nodes[competency_id].get("elo_rating", 1000.0))

    def get_prerequisites(self, competency_id: str) -> list[str]:
        """
        Get prerequisite competency IDs for a competency.

        Args:
            competency_id: Target competency.

        Returns:
            List of prerequisite competency IDs.
        """
        if competency_id not in self._graph:
            return []
        return list(self._graph.predecessors(competency_id))

    def get_dependents(self, competency_id: str) -> list[str]:
        """
        Get competencies that depend on this one.

        Args:
            competency_id: Source competency.

        Returns:
            List of dependent competency IDs.
        """
        if competency_id not in self._graph:
            return []
        return list(self._graph.successors(competency_id))

    def build_skill_graph_schema(
        self,
        user_id: int,
        competency_scores: dict[str, CompetencyScore],
    ) -> SkillGraph:
        """
        Build a SkillGraph schema for visualization.

        Args:
            user_id: User this graph belongs to.
            competency_scores: Map of competency_id to CompetencyScore.

        Returns:
            SkillGraph ready for visualization.
        """
        nodes = []
        edges = []

        for comp_id, comp in self._competencies.items():
            score = competency_scores.get(comp_id)
            confidence = score.confidence if score else 0.0

            color = self._confidence_to_color(confidence)

            node = SkillGraphNode(
                id=comp_id,
                label=comp.name,
                confidence=confidence,
                color=color,
                size=20 + int(confidence * 30),
                parent=comp.parent_id,
            )
            nodes.append(node)

        for source, target, data in self._graph.edges(data=True):
            edge = SkillGraphEdge(
                source=source,
                target=target,
                relationship=data.get("relationship", "prerequisite"),
                strength=data.get("strength", 1.0),
            )
            edges.append(edge)

        return SkillGraph(
            user_id=user_id,
            nodes=nodes,
            edges=edges,
        )

    def get_weakest_competencies(
        self,
        competency_scores: dict[str, CompetencyScore],
        role: str,
        top_n: int = 5,
    ) -> list[tuple[str, float, float]]:
        """
        Get the weakest competencies weighted by role relevance.

        Args:
            competency_scores: Map of competency_id to CompetencyScore.
            role: Job role for relevance weighting.
            top_n: Number of weakest to return.

        Returns:
            List of (competency_id, gap, role_relevance) tuples
            sorted by weighted gap descending.
        """
        gaps = []

        for comp_id, comp in self._competencies.items():
            role_relevance = comp.role_relevance.get(role, 0.0)
            if role_relevance < 0.3:
                continue

            score = competency_scores.get(comp_id)
            current_confidence = score.confidence if score else 0.0
            target_confidence = config.get_float(
                "app_config", "competency.readiness_threshold", 0.7
            )

            gap = max(0.0, target_confidence - current_confidence)
            weighted_gap = gap * role_relevance

            gaps.append((comp_id, gap, role_relevance, weighted_gap))

        # Sort by weighted gap descending
        gaps.sort(key=lambda x: x[3], reverse=True)

        return [(comp_id, gap, relevance) for comp_id, gap, relevance, _ in gaps[:top_n]]

    def _confidence_to_color(self, confidence: float) -> str:
        """
        Map confidence score to visualization color.

        Args:
            confidence: Confidence 0.0-1.0.

        Returns:
            Hex color string.
        """
        if confidence >= self._high_threshold:
            return self._color_high
        elif confidence >= self._medium_threshold:
            return self._color_medium
        else:
            return self._color_low

    def competency_count(self) -> int:
        """Get total number of loaded competencies."""
        return len(self._competencies)

    def has_competency(self, competency_id: str) -> bool:
        """Check if competency is loaded."""
        return competency_id in self._competencies
