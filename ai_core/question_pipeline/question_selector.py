"""
Question selector.

Selects appropriate interview questions based on
job role, phase, difficulty, and already-asked question IDs.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Optional

from schemas.question_schema import (
    DifficultyLevel,
    InterviewPhase,
    Question,
    QuestionType,
)


class QuestionSelector:
    """
    Selects interview questions from the question bank.

    Loads all questions from data/questions/ and provides
    filtered, randomized selection based on session context.
    """

    def __init__(self) -> None:
        """Load all questions from JSON files."""
        self._questions: list[Question] = []
        self._by_role: dict[str, list[Question]] = {}
        self._data_path = (
            Path(__file__).parent.parent.parent / "data" / "questions"
        )
        self._load_all()

    def _load_all(self) -> None:
        """Load questions from all role files."""
        role_files = [
            ("software_engineer.json", "Software Engineer"),
            ("data_analyst.json", "Data Analyst"),
            ("ai_engineer.json", "AI Engineer"),
        ]

        for filename, role_name in role_files:
            filepath = self._data_path / filename
            if not filepath.exists():
                continue

            with open(filepath, "r") as f:
                raw = json.load(f)

            questions = []
            for q in raw.get("questions", []):
                question = Question(
                    id=q["id"],
                    competency_id=q["competency_id"],
                    question_text=q["question_text"],
                    question_type=QuestionType(q["question_type"]),
                    difficulty=DifficultyLevel(q["difficulty"]),
                    elo_difficulty=q.get("elo_difficulty", 1200.0),
                    category=q.get("category", "General"),
                    required_concepts=q.get("required_concepts", []),
                    optional_concepts=q.get("optional_concepts", []),
                    sample_answer=q.get("sample_answer", ""),
                    rubric_id=q.get("rubric_id", "rubric_technical_standard"),
                    follow_up_hints=q.get("follow_up_hints", []),
                    role_tags=q.get("role_tags", []),
                )
                questions.append(question)
                self._questions.append(question)

            self._by_role[role_name] = questions

    def select_first_question(
        self,
        job_role: str,
        phase: InterviewPhase = InterviewPhase.INTRODUCTION,
    ) -> Optional[Question]:
        """
        Select the opening question for an interview.

        Args:
            job_role: Target job role.
            phase: Interview phase (usually INTRODUCTION).

        Returns:
            Selected Question or None if none found.
        """
        candidates = self._get_candidates(
            job_role=job_role,
            question_type=QuestionType.HR,
            difficulty=DifficultyLevel.BEGINNER,
            exclude_ids=[],
        )

        if not candidates:
            candidates = self._by_role.get(job_role, self._questions)

        if not candidates:
            return None

        return random.choice(candidates)

    def select_question(
        self,
        job_role: str,
        phase: InterviewPhase,
        difficulty: DifficultyLevel,
        exclude_ids: list[str],
    ) -> Optional[Question]:
        """
        Select a question matching all criteria.

        Args:
            job_role: Target job role.
            phase: Current interview phase.
            difficulty: Recommended difficulty level.
            exclude_ids: Question IDs to exclude.

        Returns:
            Selected Question or None if none found.
        """
        q_type = (
            QuestionType.HR
            if phase in (
                InterviewPhase.INTRODUCTION,
                InterviewPhase.BEHAVIORAL,
                InterviewPhase.CLOSING,
            )
            else QuestionType.TECHNICAL
        )

        # Try exact difficulty match first
        candidates = self._get_candidates(
            job_role=job_role,
            question_type=q_type,
            difficulty=difficulty,
            exclude_ids=exclude_ids,
        )

        # Fall back to any difficulty of same type
        if not candidates:
            candidates = self._get_candidates(
                job_role=job_role,
                question_type=q_type,
                difficulty=None,
                exclude_ids=exclude_ids,
            )

        # Fall back to any question not yet asked
        if not candidates:
            candidates = [
                q for q in self._questions
                if q.id not in exclude_ids
            ]

        if not candidates:
            return None

        return random.choice(candidates)

    def get_questions_for_role(
        self,
        job_role: str,
        question_type: Optional[QuestionType] = None,
    ) -> list[Question]:
        """
        Get all questions for a role.

        Args:
            job_role: Target job role.
            question_type: Filter by type if provided.

        Returns:
            List of matching Questions.
        """
        questions = self._by_role.get(job_role, [])

        if question_type:
            questions = [q for q in questions if q.question_type == question_type]

        return questions

    def _get_candidates(
        self,
        job_role: str,
        question_type: QuestionType,
        difficulty: Optional[DifficultyLevel],
        exclude_ids: list[str],
    ) -> list[Question]:
        """
        Get candidate questions matching filters.

        Args:
            job_role: Target job role.
            question_type: technical or hr.
            difficulty: Difficulty filter, None for any.
            exclude_ids: IDs to exclude.

        Returns:
            Filtered candidate questions.
        """
        pool = self._by_role.get(job_role, self._questions)

        candidates = [
            q for q in pool
            if q.question_type == question_type
            and q.id not in exclude_ids
            and (difficulty is None or q.difficulty == difficulty)
        ]

        return candidates
