"""
Practice question generator.

Suggests practice questions for identified skill gaps
based on the question bank and competency mapping.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from schemas.competency_schema import CompetencyGap
from schemas.question_schema import Question, QuestionType, DifficultyLevel


class PracticeGenerator:
    """
    Generates practice question suggestions for skill gaps.

    Loads questions from the question bank and matches them
    to competency gaps, returning the most relevant ones.
    """

    def __init__(self) -> None:
        """Load questions from JSON data files."""
        self._questions: list[Question] = []
        self._questions_by_competency: dict[str, list[Question]] = {}
        self._data_path = (
            Path(__file__).parent.parent.parent / "data" / "questions"
        )
        self._load_all_questions()

    def _load_all_questions(self) -> None:
        """Load questions from all role JSON files."""
        role_files = [
            "software_engineer.json",
            "data_analyst.json",
            "ai_engineer.json",
        ]

        for role_file in role_files:
            filepath = self._data_path / role_file
            if not filepath.exists():
                continue

            with open(filepath, "r") as f:
                raw_data = json.load(f)

            for q_data in raw_data.get("questions", []):
                question = Question(
                    id=q_data["id"],
                    competency_id=q_data["competency_id"],
                    question_text=q_data["question_text"],
                    question_type=QuestionType(q_data["question_type"]),
                    difficulty=DifficultyLevel(q_data["difficulty"]),
                    elo_difficulty=q_data.get("elo_difficulty", 1200.0),
                    category=q_data.get("category", "General"),
                    required_concepts=q_data.get("required_concepts", []),
                    optional_concepts=q_data.get("optional_concepts", []),
                    sample_answer=q_data.get("sample_answer", ""),
                    rubric_id=q_data.get("rubric_id", "rubric_technical_standard"),
                    follow_up_hints=q_data.get("follow_up_hints", []),
                    role_tags=q_data.get("role_tags", []),
                )

                self._questions.append(question)

                comp_id = question.competency_id
                if comp_id not in self._questions_by_competency:
                    self._questions_by_competency[comp_id] = []
                self._questions_by_competency[comp_id].append(question)

        print(f"Loaded {len(self._questions)} practice questions")

    def get_practice_questions(
        self,
        gap: CompetencyGap,
        top_n: int = 3,
        exclude_ids: list[str] | None = None,
    ) -> list[Question]:
        """
        Get practice questions for a specific competency gap.

        Args:
            gap: The skill gap to address.
            top_n: Maximum questions to return.
            exclude_ids: Question IDs already asked in this session.

        Returns:
            List of Questions ordered by difficulty appropriateness.
        """
        if exclude_ids is None:
            exclude_ids = []

        # Get questions for this competency
        candidates = self._questions_by_competency.get(
            gap.competency_id, []
        )

        # Filter out already asked questions
        candidates = [q for q in candidates if q.id not in exclude_ids]

        if not candidates:
            return []

        # Sort by difficulty appropriateness
        sorted_questions = self._sort_by_difficulty(
            questions=candidates,
            current_confidence=gap.current_confidence,
        )

        return sorted_questions[:top_n]

    def get_practice_for_multiple_gaps(
        self,
        gaps: list[CompetencyGap],
        questions_per_gap: int = 2,
        exclude_ids: list[str] | None = None,
    ) -> dict[str, list[Question]]:
        """
        Get practice questions for multiple gaps.

        Args:
            gaps: List of skill gaps.
            questions_per_gap: Questions per gap.
            exclude_ids: Already asked question IDs.

        Returns:
            Map of competency_id to list of Questions.
        """
        result: dict[str, list[Question]] = {}

        for gap in gaps:
            questions = self.get_practice_questions(
                gap=gap,
                top_n=questions_per_gap,
                exclude_ids=exclude_ids or [],
            )
            if questions:
                result[gap.competency_id] = questions

        return result

    def get_follow_up_hints(self, question: Question) -> list[str]:
        """
        Get follow-up question hints for a specific question.

        Args:
            question: The answered question.

        Returns:
            List of follow-up hint strings.
        """
        return question.follow_up_hints

    def _sort_by_difficulty(
        self,
        questions: list[Question],
        current_confidence: float,
    ) -> list[Question]:
        """
        Sort questions by difficulty appropriateness.

        Target slightly above current competency level to
        provide appropriate challenge.

        Args:
            questions: Candidate questions.
            current_confidence: Current confidence 0.0-1.0.

        Returns:
            Sorted questions.
        """
        difficulty_targets = {
            DifficultyLevel.BEGINNER: 0.25,
            DifficultyLevel.INTERMEDIATE: 0.55,
            DifficultyLevel.ADVANCED: 0.80,
            DifficultyLevel.EXPERT: 0.95,
        }

        # Target slightly above current level
        target = min(current_confidence + 0.2, 0.9)

        def score(q: Question) -> float:
            level = difficulty_targets.get(q.difficulty, 0.5)
            return -abs(level - target)

        return sorted(questions, key=score, reverse=True)

    def question_count(self) -> int:
        """Get total number of loaded questions."""
        return len(self._questions)

    def competency_count(self) -> int:
        """Get number of competencies with questions."""
        return len(self._questions_by_competency)
