"""
Demo script.

Runs a complete interview session end to end
without any UI, demonstrating the full AI pipeline
in a single terminal session.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Demo Data

DEMO_ANSWERS = [
    {
        "question_id": "q_se_oop_001",
        "competency_id": "comp_se_oop",
        "question_text": "Explain the four pillars of Object Oriented Programming.",
        "question_type": "technical",
        "sample_answer": (
            "The four pillars of OOP are Encapsulation, Inheritance, "
            "Polymorphism, and Abstraction. Encapsulation bundles data "
            "and methods within a class. Inheritance allows child classes "
            "to reuse parent class properties. Polymorphism enables one "
            "interface to behave differently based on object type. "
            "Abstraction hides implementation details."
        ),
        "required_concepts": [
            "encapsulation", "inheritance", "polymorphism", "abstraction"
        ],
        "elo_difficulty": 1200.0,
        "user_answer": (
            "OOP has four pillars. Encapsulation hides the internal state "
            "of a class and only exposes what is necessary. Inheritance "
            "allows a child class to reuse and extend the behavior of a "
            "parent class, because this reduces code duplication. "
            "Polymorphism means the same method can behave differently "
            "depending on the object type, which makes code more flexible. "
            "Abstraction hides implementation complexity from the user. "
            "For example, in Python I used inheritance to create a base "
            "Animal class and extended it with Dog and Cat subclasses."
        ),
    },
    {
        "question_id": "q_se_db_001",
        "competency_id": "comp_se_databases",
        "question_text": "What are ACID properties in database transactions?",
        "question_type": "technical",
        "sample_answer": (
            "ACID stands for Atomicity, Consistency, Isolation, Durability. "
            "Atomicity means all operations in a transaction succeed or all fail. "
            "Consistency means the database moves from one valid state to another. "
            "Isolation means concurrent transactions do not interfere. "
            "Durability means committed data persists even after failures."
        ),
        "required_concepts": [
            "atomicity", "consistency", "isolation", "durability", "transaction"
        ],
        "elo_difficulty": 1300.0,
        "user_answer": (
            "Transactions are reliable because databases prevent corruption."
        ),
    },
    {
        "question_id": "q_se_hr_001",
        "competency_id": "comp_se_behavioral",
        "question_text": "Tell me about yourself and your technical background.",
        "question_type": "hr",
        "sample_answer": (
            "I am a software engineering graduate with strong Python skills. "
            "I have worked on REST APIs and machine learning projects. "
            "My goals are to grow as a backend engineer."
        ),
        "required_concepts": ["background", "skills", "goals"],
        "elo_difficulty": 900.0,
        "user_answer": (
            "I am a computer science graduate with two years of experience "
            "building web applications using Python and Django. I built a "
            "REST API for an e-commerce platform that handled 5,000 daily "
            "users and reduced response time by 30% through query optimization. "
            "My goal is to grow into a senior backend engineer role where "
            "I can design scalable systems and mentor junior developers."
        ),
    },
]


def run_demo() -> None:
    """Run complete demo interview session."""
    print("=" * 65)
    print("  AI INTERVIEW ASSISTANT - DEMO SESSION")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 65)

    # Import components
    from database.db_setup import init_db, SessionLocal
    from database.repositories import UserRepository, SessionRepository
    from services.evaluation_service import EvaluationService
    from services.competency_service import CompetencyService
    from services.recommendation_service import RecommendationService
    from services.analytics_service import AnalyticsService
    from schemas.answer_schema import AnswerInput
    from schemas.question_schema import QuestionType

    # Init database
    init_db()
    db = SessionLocal()

    try:
        # Create demo user
        print("\n  Setting up demo user...")
        user_repo = UserRepository(db)
        existing = user_repo.get_by_username("demo_runner")
        if existing:
            user = existing
        else:
            user = user_repo.create(
                username="demo_runner",
                email="demo_runner@demo.com",
                password="demo123",
                full_name="Demo Runner",
                target_role="Software Engineer",
            )
        db.flush()
        print(f"  [PASS] User: {user.username} (id={user.id})")

        # Create session
        session_repo = SessionRepository(db)
        interview_session = session_repo.create(
            user_id=user.id,
            job_role="Software Engineer",
            difficulty="intermediate",
            total_questions=len(DEMO_ANSWERS),
        )
        db.flush()
        print(f"  [PASS] Session: id={interview_session.id}")

        # Run evaluations
        eval_service = EvaluationService(db)
        all_scores = []
        technical_scores = []
        hr_scores = []

        print(f"\n  Running {len(DEMO_ANSWERS)} interview questions...\n")

        for i, answer_data in enumerate(DEMO_ANSWERS, 1):
            print(f"  {'-'*60}")
            print(f"  Q{i}: {answer_data['question_text']}")
            print(f"  Type: {answer_data['question_type'].upper()}")
            print(
                f"  Answer: \"{answer_data['user_answer'][:80]}"
                f"{'...' if len(answer_data['user_answer']) > 80 else ''}\""
            )

            answer_input = AnswerInput(
                session_id=interview_session.id,
                user_id=user.id,
                question_id=answer_data["question_id"],
                competency_id=answer_data["competency_id"],
                question_text=answer_data["question_text"],
                question_type=QuestionType(answer_data["question_type"]),
                sample_answer=answer_data["sample_answer"],
                required_concepts=answer_data["required_concepts"],
                optional_concepts=[],
                rubric_id=(
                    "rubric_hr_standard"
                    if answer_data["question_type"] == "hr"
                    else "rubric_technical_standard"
                ),
                user_answer=answer_data["user_answer"],
                time_taken=45,
            )

            start = time.time()
            result = eval_service.evaluate_answer(
                answer_input,
                question_elo=answer_data["elo_difficulty"],
            )
            elapsed = (time.time() - start) * 1000

            ev = result.evaluation
            score = ev.scores.weighted_final

            all_scores.append(score)
            if answer_data["question_type"] == "technical":
                technical_scores.append(score)
            else:
                hr_scores.append(score)

            print(f"\n  [INFO] Evaluation Result ({elapsed:.0f}ms):")
            print(f"     Final Score:     {score:.1f}/100")
            print(f"     Grade:           {ev.grade.value}")
            print(f"     Semantic:        {ev.scores.semantic:.1f}")
            print(f"     Concept:         {ev.scores.concept:.1f}")
            print(f"     Communication:   {ev.scores.communication:.1f}")
            print(f"     Evidence:        {ev.scores.evidence:.1f}")
            print(f"     Reasoning:       {ev.scores.reasoning:.1f}")

            if ev.evidence.matched_concepts:
                print(
                    f"     [PASS] Found:    "
                    f"{', '.join(ev.evidence.matched_concepts[:3])}"
                )
            if ev.evidence.missing_concepts:
                print(
                    f"     [FAIL] Missing:  "
                    f"{', '.join(ev.evidence.missing_concepts[:3])}"
                )

            print(f"     [TIP]            {ev.explanation.improvement_tip[:80]}...")
            print(f"     Delta Comp:      {ev.competency_delta:+.4f}")

        # Complete session
        overall = sum(all_scores) / len(all_scores)
        technical = (
            sum(technical_scores) / len(technical_scores)
            if technical_scores else 0
        )
        hr = sum(hr_scores) / len(hr_scores) if hr_scores else 0

        session_repo.complete_session(
            session_id=interview_session.id,
            overall_score=round(overall, 2),
            technical_score=round(technical, 2),
            hr_score=round(hr, 2),
            readiness_level=(
                "excellent" if overall >= 85
                else "good" if overall >= 70
                else "average" if overall >= 50
                else "poor"
            ),
            answered_questions=len(all_scores),
        )

        print(f"\n  {'='*60}")
        print(f"  SESSION COMPLETE")
        print(f"  {'='*60}")
        print(f"  Overall Score:    {overall:.1f}/100")
        print(f"  Technical Score:  {technical:.1f}/100")
        print(f"  HR Score:         {hr:.1f}/100")
        print(f"  Questions:        {len(all_scores)}")

        # Skill gaps
        comp_service = CompetencyService(db)
        gaps = comp_service.get_skill_gaps(user.id, "Software Engineer", top_n=3)

        if gaps:
            print(f"\n  Top Skill Gaps:")
            for gap in gaps:
                print(
                    f"    [{gap.priority.value.upper():<6}] "
                    f"{gap.competency_name:<30} "
                    f"gap={gap.gap:.2f}"
                )

        # Readiness
        readiness = comp_service.get_overall_readiness(user.id, "Software Engineer")
        print(f"\n  Interview Readiness: {readiness:.1f}%")

        # Recommendations
        rec_service = RecommendationService(db)
        next_steps = rec_service.get_next_steps(
            user_id=user.id,
            session_id=interview_session.id,
            gaps=gaps,
            top_n=2,
        )

        if next_steps:
            print(f"\n  Immediate Next Steps:")
            for step in next_steps:
                print(f"    * {step.title}")
                if step.resource:
                    print(f"      -> {step.resource.url}")

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"\n  [FAIL] Demo failed: {e}")
        raise
    finally:
        db.close()

    print(f"\n{'='*65}")
    print("  Demo complete. Full system is working end-to-end.")
    print("=" * 65)


if __name__ == "__main__":
    run_demo()
