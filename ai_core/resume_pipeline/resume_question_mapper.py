"""
Resume question mapper.

Maps extracted resume skills to competencies and
generates customized interview questions that verify
the candidate's claimed skills.
"""

from __future__ import annotations

import json
from pathlib import Path

from ai_core.skill_pipeline.competency_graph import CompetencyGraph
from schemas.question_schema import Question, QuestionType, DifficultyLevel
from schemas.resume_schema import ExtractedSkill


class ResumeQuestionMapper:
    """
    Maps resume skills to interview questions.

    When a candidate claims a skill on their resume, the interview
    should verify that claim with targeted questions about that skill.
    """

    # Skill name (canonical) -> competency ID
    SKILL_COMPETENCY_MAP: dict[str, str] = {
        # Software Engineering
        "Python": "comp_se_oop",
        "JavaScript": "comp_se_rest_api",
        "TypeScript": "comp_se_rest_api",
        "Java": "comp_se_oop",
        "C++": "comp_se_oop",
        "React.js": "comp_se_rest_api",
        "Node.js": "comp_se_rest_api",
        "REST API": "comp_se_rest_api",
        "GraphQL": "comp_se_rest_api",
        "Django": "comp_se_rest_api",
        "Flask": "comp_se_rest_api",
        "FastAPI": "comp_se_rest_api",
        "SQL": "comp_se_databases",
        "PostgreSQL": "comp_se_databases",
        "MySQL": "comp_se_databases",
        "MongoDB": "comp_se_databases",
        "Redis": "comp_se_databases",
        "Docker": "comp_se_system_design",
        "Kubernetes": "comp_se_system_design",
        "AWS": "comp_se_system_design",
        "GCP": "comp_se_system_design",
        "Microsoft Azure": "comp_se_system_design",
        "Git": "comp_se_version_control",
        "GitHub": "comp_se_version_control",
        "GitLab": "comp_se_version_control",
        "CI/CD": "comp_se_version_control",
        "Object-Oriented Programming": "comp_se_oop",
        "Test-Driven Development": "comp_se_testing",
        "Microservices": "comp_se_system_design",

        # AI Engineering
        "Machine Learning": "comp_ai_ml_fundamentals",
        "Deep Learning": "comp_ai_deep_learning",
        "NLP": "comp_ai_nlp",
        "TensorFlow": "comp_ai_deep_learning",
        "PyTorch": "comp_ai_deep_learning",
        "Scikit-learn": "comp_ai_ml_fundamentals",
        "Hugging Face": "comp_ai_nlp",
        "Computer Vision": "comp_ai_model_evaluation",
        "OpenCV": "comp_ai_model_evaluation",
        "Artificial Intelligence": "comp_ai_ml_fundamentals",

        # Data Analyst
        "Pandas": "comp_da_python",
        "NumPy": "comp_da_python",
        "Matplotlib": "comp_da_python",
        "Plotly": "comp_da_python",
        "Data Analysis": "comp_da_eda",
        "Statistics": "comp_da_statistics",
        "Tableau": "comp_da_visualization",
        "Power BI": "comp_da_visualization",
        "BigQuery": "comp_da_sql",
        "Snowflake": "comp_da_sql",
    }

    # Follow-up question templates per skill
    _FOLLOW_UPS: dict[str, str] = {
        "Python": (
            "You mentioned Python. Can you walk me through "
            "a specific project where you used it and what challenges you faced?"
        ),
        "Machine Learning": (
            "You mentioned machine learning. "
            "What evaluation metrics did you use and why were they appropriate?"
        ),
        "Docker": (
            "You mentioned Docker. "
            "Can you explain how containerization helped your project?"
        ),
        "React.js": (
            "You mentioned React. How did you manage state in your application?"
        ),
        "SQL": (
            "You mentioned SQL. "
            "Can you describe a complex query or optimization you implemented?"
        ),
        "AWS": (
            "You mentioned AWS. "
            "Which services have you used and for what specific purpose?"
        ),
        "PostgreSQL": (
            "You mentioned PostgreSQL. "
            "How did you design the schema and handle indexing?"
        ),
        "NLP": (
            "You mentioned NLP. "
            "Which preprocessing steps did you apply and why?"
        ),
    }

    def __init__(self) -> None:
        """Initialize with question bank from all role JSON files."""
        self._questions: list[Question] = []
        self._questions_by_competency: dict[str, list[Question]] = {}
        self._data_path = (
            Path(__file__).parent.parent.parent / "data" / "questions"
        )
        self._graph = CompetencyGraph()
        self._load_questions()

    def _load_questions(self) -> None:
        """Load questions from all available role JSON files."""
        role_files = [
            "software_engineer.json",
            "data_analyst.json",
            "ai_engineer.json",
        ]

        for filename in role_files:
            filepath = self._data_path / filename
            if not filepath.exists():
                continue

            with open(filepath, "r") as f:
                raw = json.load(f)

            for q_data in raw.get("questions", []):
                try:
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
                        rubric_id=q_data.get(
                            "rubric_id", "rubric_technical_standard"
                        ),
                        follow_up_hints=q_data.get("follow_up_hints", []),
                        role_tags=q_data.get("role_tags", []),
                    )

                    comp_id = question.competency_id
                    self._questions_by_competency.setdefault(
                        comp_id, []
                    ).append(question)
                    self._questions.append(question)

                except Exception:
                    continue

    def map_skills_to_competencies(
        self,
        skills: list[ExtractedSkill],
    ) -> dict[str, list[str]]:
        """
        Map extracted skills to competency IDs.

        Args:
            skills: Skills extracted from resume.

        Returns:
            Dict of competency_id to list of matched skill names.
        """
        competency_map: dict[str, list[str]] = {}

        for skill in skills:
            comp_id = self.SKILL_COMPETENCY_MAP.get(skill.normalized)
            if comp_id:
                competency_map.setdefault(comp_id, []).append(
                    skill.normalized
                )

        return competency_map

    def get_targeted_questions(
        self,
        skills: list[ExtractedSkill],
        questions_per_skill: int = 1,
        difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
    ) -> list[dict]:
        """
        Get targeted questions for claimed resume skills.

        Questions are chosen to verify specific skill claims,
        with a note explaining the targeting rationale.

        Args:
            skills: Skills extracted from resume.
            questions_per_skill: Questions to select per skill (usually 1).
            difficulty: Target difficulty level.

        Returns:
            List of dicts with question and targeting context.
        """
        targeted: list[dict] = []
        seen_question_ids: set[str] = set()
        seen_competencies: set[str] = set()

        # Highest confidence claims are verified first
        sorted_skills = sorted(
            skills, key=lambda s: s.confidence, reverse=True
        )

        for skill in sorted_skills:
            comp_id = self.SKILL_COMPETENCY_MAP.get(skill.normalized)
            if not comp_id or comp_id in seen_competencies:
                continue

            questions = self._questions_by_competency.get(comp_id, [])
            if not questions:
                continue

            # Prefer matching difficulty first
            candidates = [
                q for q in questions
                if q.difficulty == difficulty
                and q.id not in seen_question_ids
            ]
            if not candidates:
                candidates = [
                    q for q in questions
                    if q.id not in seen_question_ids
                ]

            if not candidates:
                continue

            question = candidates[0]
            seen_question_ids.add(question.id)
            seen_competencies.add(comp_id)

            targeted.append({
                "question": {
                    "id": question.id,
                    "question_text": question.question_text,
                    "question_type": question.question_type.value,
                    "difficulty": question.difficulty.value,
                    "competency_id": question.competency_id,
                    "required_concepts": question.required_concepts,
                    "sample_answer": question.sample_answer,
                    "rubric_id": question.rubric_id,
                    "elo_difficulty": question.elo_difficulty,
                },
                "targeting_reason": (
                    f"You listed '{skill.normalized}' on your resume "
                    f"(detected in: {skill.source_section}). "
                    f"This question verifies your claimed knowledge."
                ),
                "skill_claimed": skill.normalized,
                "skill_confidence": skill.confidence,
            })

        return targeted

    def get_follow_up_for_skill(
        self,
        skill_name: str,
    ) -> str | None:
        """
        Get a follow-up question for a skill mentioned in an answer.

        Args:
            skill_name: Canonical skill name the candidate mentioned.

        Returns:
            Follow-up question string or None if not available.
        """
        return self._FOLLOW_UPS.get(skill_name)

    def get_detected_competency_ids(
        self,
        skills: list[ExtractedSkill],
    ) -> list[str]:
        """
        Get list of unique competency IDs detected from skills.

        Args:
            skills: Extracted and normalized skills.

        Returns:
            Unique list of competency IDs.
        """
        seen: set[str] = set()
        result: list[str] = []

        for skill in skills:
            comp_id = self.SKILL_COMPETENCY_MAP.get(skill.normalized)
            if comp_id and comp_id not in seen:
                seen.add(comp_id)
                result.append(comp_id)

        return result
