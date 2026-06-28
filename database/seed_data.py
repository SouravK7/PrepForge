"""
Database seed data.

Populates the database with initial data for development
and testing. Includes demo users, competency scores,
and sample sessions. Safe to run on an empty database.

Usage:
    python -m database.seed_data
"""

from __future__ import annotations

from database.db_setup import SessionLocal, init_db
from database.repositories import (
    UserRepository,
    SessionRepository,
    AnswerRepository,
    CompetencyScoreRepository,
)
from schemas.competency_schema import CompetencyScore as CompetencyScoreSchema


def seed_demo_users(session) -> dict[str, int]:
    """
    Seed demo user accounts.

    Args:
        session: SQLAlchemy session.

    Returns:
        Dict of username to user_id.
    """
    user_repo = UserRepository(session)

    demo_users = [
        {
            "username": "demo_student",
            "email": "demo@prepforge.ai",
            "password": "demo1234",
            "full_name": "Demo Student",
            "target_role": "Software Engineer",
            "experience_level": "entry_level",
        },
        {
            "username": "alice",
            "email": "alice@prepforge.ai",
            "password": "alice1234",
            "full_name": "Alice Chen",
            "target_role": "Data Analyst",
            "experience_level": "mid_level",
        },
        {
            "username": "bob",
            "email": "bob@prepforge.ai",
            "password": "bob1234",
            "full_name": "Bob Kumar",
            "target_role": "AI Engineer",
            "experience_level": "entry_level",
        },
    ]

    user_ids: dict[str, int] = {}
    for user_data in demo_users:
        existing = user_repo.get_by_username(user_data["username"])
        if existing:
            user_ids[user_data["username"]] = existing.id
            print(f"  User already exists: {user_data['username']}")
        else:
            user = user_repo.create(**user_data)
            user_ids[user_data["username"]] = user.id
            print(f"  Created user: {user_data['username']} (id={user.id})")

    return user_ids


def seed_competency_scores(session, user_ids: dict[str, int]) -> None:
    """
    Seed initial competency confidence scores for demo users.

    Args:
        session: SQLAlchemy session.
        user_ids: Dict of username to user_id.
    """
    score_repo = CompetencyScoreRepository(session)

    # Demo student: various levels across SE competencies
    demo_id = user_ids.get("demo_student", 1)
    se_scores = [
        ("comp_se_oop", 0.45, 1050.0, 3),
        ("comp_se_databases", 0.30, 980.0, 2),
        ("comp_se_algorithms", 0.20, 920.0, 1),
        ("comp_se_system_design", 0.10, 880.0, 0),
        ("comp_se_behavioral", 0.60, 1100.0, 4),
    ]

    for comp_id, confidence, elo, evidence_count in se_scores:
        schema = CompetencyScoreSchema(
            user_id=demo_id,
            competency_id=comp_id,
            confidence=confidence,
            elo_rating=elo,
            evidence_count=evidence_count,
            improvement_trend=0.05,
        )
        score_repo.upsert(schema)

    print(f"  Seeded {len(se_scores)} competency scores for demo_student")


def seed_demo_session(session, user_ids: dict[str, int]) -> None:
    """
    Seed a completed interview session for demo user.

    Args:
        session: SQLAlchemy session.
        user_ids: Dict of username to user_id.
    """
    session_repo = SessionRepository(session)
    answer_repo = AnswerRepository(session)

    demo_id = user_ids.get("demo_student", 1)

    # Create a completed session
    interview_session = session_repo.create(
        user_id=demo_id,
        job_role="Software Engineer",
        difficulty="intermediate",
        experience_level="entry_level",
        total_questions=5,
    )

    # Complete it with scores
    session_repo.complete_session(
        session_id=interview_session.id,
        overall_score=58.5,
        technical_score=52.0,
        hr_score=72.0,
        readiness_level="average",
        answered_questions=5,
    )

    # Add a sample answer
    answer_repo.create(
        session_id=interview_session.id,
        user_id=demo_id,
        question_id="q_se_oop_001",
        competency_id="comp_se_oop",
        question_text="Explain the four pillars of Object Oriented Programming.",
        question_type="technical",
        answer_text=(
            "OOP has four pillars: encapsulation, inheritance, "
            "polymorphism, and abstraction. Encapsulation means hiding "
            "data. Inheritance allows classes to inherit from others. "
            "Polymorphism lets objects take multiple forms. Abstraction "
            "hides implementation details."
        ),
        time_taken=120,
    )

    print(f"  Created demo session (id={interview_session.id}) for demo_student")


def run_seed() -> None:
    """
    Run the full seed sequence.

    Creates all demo data in order:
    1. Demo users
    2. Competency scores
    3. Demo sessions
    """
    print("\n=== Running Database Seed ===\n")

    init_db()

    session = SessionLocal()
    try:
        print("Seeding users...")
        user_ids = seed_demo_users(session)

        print("\nSeeding competency scores...")
        seed_competency_scores(session, user_ids)

        print("\nSeeding demo session...")
        seed_demo_session(session, user_ids)

        session.commit()
        print("\n=== Seed Complete ===")

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Seed failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_seed()
