"""
Integration verification script.

Tests that all components work together correctly
in a complete end-to-end flow without starting
the web servers.
"""

from __future__ import annotations

import sys


def verify_imports() -> bool:
    """Verify all major imports work."""
    print("  [1/6] Verifying imports...")

    imports = [
        ("ai_core.shared", "ModelManager, EmbeddingService, TextProcessor"),
        ("ai_core.evaluation_pipeline", "EvaluationOrchestrator"),
        ("ai_core.skill_pipeline", "CompetencyGraph, EloEstimator, SkillGapAnalyzer"),
        ("ai_core.recommendation_pipeline", "Recommender"),
        ("ai_core.resume_pipeline", "ResumeParser, SkillExtractor"),
        ("ai_core.question_pipeline.question_selector", "QuestionSelector"),
        ("schemas", "AnswerInput, EvaluationOutput, CompetencyGap"),
        ("database", "init_db, get_session, UserRepository"),
        ("services", "InterviewService, EvaluationService, CompetencyService"),
        ("api.main", "app"),
        ("frontend.streamlit_app", "main"),
        ("benchmark.run_benchmark", "BenchmarkRunner"),
        ("benchmark.ablation_runner", "AblationRunner"),
    ]

    failed = []
    for module, components in imports:
        try:
            __import__(module)
        except ImportError as e:
            failed.append(f"{module}: {e}")

    if failed:
        print(f"  [FAIL] Import failures:")
        for f in failed:
            print(f"     {f}")
        return False

    print(f"  [PASS] All {len(imports)} module imports successful")
    return True


def verify_evaluation_pipeline() -> bool:
    """Verify evaluation pipeline produces valid output."""
    print("  [2/6] Verifying evaluation pipeline...")

    from ai_core.evaluation_pipeline import EvaluationOrchestrator
    from schemas.answer_schema import AnswerInput
    from schemas.question_schema import QuestionType

    orchestrator = EvaluationOrchestrator()

    test_cases = [
        (
            "excellent",
            "OOP has four pillars: Encapsulation hides data, "
            "Inheritance allows code reuse, Polymorphism enables "
            "different behaviors, Abstraction hides complexity. "
            "For example in Python I used inheritance to build "
            "a hierarchy of shapes.",
        ),
        (
            "poor",
            "OOP is programming.",
        ),
    ]

    scores = {}
    for label, answer_text in test_cases:
        answer = AnswerInput(
            session_id=0, user_id=0,
            question_id="verify_test", competency_id="comp_se_oop",
            question_text="Explain OOP.",
            question_type=QuestionType.TECHNICAL,
            sample_answer="OOP has encapsulation, inheritance, polymorphism, abstraction.",
            required_concepts=["encapsulation", "inheritance", "polymorphism", "abstraction"],
            optional_concepts=[], rubric_id="rubric_technical_standard",
            user_answer=answer_text,
        )
        result = orchestrator.evaluate(answer)
        scores[label] = result.scores.weighted_final

    if scores["excellent"] <= scores["poor"]:
        print("  [FAIL] Excellent answer should score higher than poor answer")
        return False

    if not all(
        result.explanation.improvement_tip
        for result in [orchestrator.evaluate(AnswerInput(
            session_id=0, user_id=0, question_id="v", competency_id="c",
            question_text="Q", question_type=QuestionType.TECHNICAL,
            sample_answer="S", required_concepts=["x"],
            optional_concepts=[], rubric_id="rubric_technical_standard",
            user_answer="test answer text here",
        ))]
    ):
        print("  [FAIL] Improvement tip not generated")
        return False

    print(
        f"  [PASS] Evaluation works: "
        f"excellent={scores['excellent']:.1f} > poor={scores['poor']:.1f}"
    )
    return True


def verify_skill_pipeline() -> bool:
    """Verify skill pipeline produces valid output."""
    print("  [3/6] Verifying skill pipeline...")

    from ai_core.skill_pipeline import (
        CompetencyGraph, ConfidenceUpdater, EloEstimator, SkillGapAnalyzer
    )
    from schemas.competency_schema import CompetencyScore

    graph = CompetencyGraph()
    graph.load_role("software_engineer")

    if graph.competency_count() == 0:
        print("  [FAIL] No competencies loaded")
        return False

    updater = ConfidenceUpdater()
    initial = updater.create_initial_score(1, "comp_se_oop")
    updated, record = updater.update(initial, evaluation_score=80.0)

    if updated.confidence <= initial.confidence:
        print("  [FAIL] Confidence should increase for good score")
        return False

    estimator = EloEstimator()
    expected = estimator.compute_expected_score(1000.0, 1200.0)

    if not (0.0 < expected < 0.5):
        print("  [FAIL] Expected score calculation incorrect")
        return False

    comp = graph.get_competency("comp_se_oop")
    if not comp:
        print("  [FAIL] OOP competency not found")
        return False

    print(
        f"  [PASS] Skill pipeline works: "
        f"{graph.competency_count()} competencies, "
        f"confidence update delta={record.delta:+.3f}"
    )
    return True


def verify_recommendation_pipeline() -> bool:
    """Verify recommendation pipeline."""
    print("  [4/6] Verifying recommendation pipeline...")

    from ai_core.recommendation_pipeline import Recommender
    from schemas.competency_schema import CompetencyGap, PriorityEnum

    recommender = Recommender()

    gaps = [
        CompetencyGap(
            competency_id="comp_se_oop",
            competency_name="OOP",
            current_confidence=0.2,
            gap=0.5,
            priority=PriorityEnum.HIGH,
            role_relevance=0.95,
            recommended_action="Study OOP.",
        ),
    ]

    output = recommender.recommend(
        user_id=1, session_id=1,
        gaps=gaps, target_role="Software Engineer",
    )

    if output.roadmap.total_weeks == 0:
        print("  [FAIL] Roadmap generated zero weeks")
        return False

    if not output.roadmap.weekly_plans:
        print("  [FAIL] No weekly plans generated")
        return False

    print(
        f"  [PASS] Recommendation works: "
        f"{output.roadmap.total_weeks} weeks, "
        f"{len(output.top_resources)} resources"
    )
    return True


def verify_database_pipeline() -> bool:
    """Verify database operations work."""
    print("  [5/6] Verifying database pipeline...")

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.models import Base
    from database.repositories import (
        UserRepository, SessionRepository, AnswerRepository,
        EvaluationRepository, CompetencyScoreRepository,
    )
    from ai_core.evaluation_pipeline import EvaluationOrchestrator
    from schemas.answer_schema import AnswerInput
    from schemas.question_schema import QuestionType

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    db = TestSession()

    try:
        user_repo = UserRepository(db)
        user = user_repo.create("verify_user", "v@test.com", "pass")
        db.flush()

        session_repo = SessionRepository(db)
        session = session_repo.create(user.id, "Software Engineer")
        db.flush()

        answer_repo = AnswerRepository(db)
        answer = answer_repo.create(
            session.id, user.id, "q_test", "comp_se_oop",
            "Q?", "technical", "An answer.", 30
        )
        db.flush()

        eval_repo = EvaluationRepository(db)
        orchestrator = EvaluationOrchestrator()

        answer_input = AnswerInput(
            session_id=session.id, user_id=user.id,
            question_id="q_test", competency_id="comp_se_oop",
            question_text="Q?", question_type=QuestionType.TECHNICAL,
            sample_answer="OOP has encapsulation.", required_concepts=["encapsulation"],
            optional_concepts=[], rubric_id="rubric_technical_standard",
            user_answer="OOP has encapsulation and inheritance.",
        )

        eval_output = orchestrator.evaluate(answer_input)
        eval_record = eval_repo.create_from_output(eval_output, answer.id)
        db.flush()

        score_repo = CompetencyScoreRepository(db)
        from schemas.competency_schema import CompetencyScore as ScoreSchema
        score_repo.upsert(ScoreSchema(
            user_id=user.id, competency_id="comp_se_oop",
            confidence=0.5, elo_rating=1050.0,
            evidence_count=1, improvement_trend=0.05,
        ))
        db.commit()

        scores = score_repo.get_all_for_user(user.id)
        evals = eval_repo.get_session_evaluations(session.id)

        if len(scores) == 0:
            print("  [FAIL] No competency scores saved")
            return False

        if len(evals) == 0:
            print("  [FAIL] No evaluations saved")
            return False

        print(
            f"  [PASS] Database pipeline works: "
            f"{len(evals)} eval saved, "
            f"{len(scores)} competency score saved"
        )
        return True

    finally:
        db.close()
        Base.metadata.drop_all(engine)


def verify_resume_pipeline() -> bool:
    """Verify resume pipeline."""
    print("  [6/6] Verifying resume pipeline...")

    from ai_core.resume_pipeline import (
        ResumeParser, SkillExtractor, SkillNormalizer,
        ResumeConfidenceAnalyzer,
    )

    resume_text = """
    SKILLS
    Python, Machine Learning, Docker, REST API, PostgreSQL, Git

    EXPERIENCE
    Software Engineer 2022-2024
    Built machine learning pipeline using Python and scikit-learn.
    Deployed using Docker on AWS. Reduced inference time by 40%.

    EDUCATION
    B.Sc Computer Science 2018-2022
    """

    parser = ResumeParser()
    parsed = parser.parse_text(resume_text)

    extractor = SkillExtractor()
    raw_skills = extractor.extract_from_sections(parsed["sections"])

    normalizer = SkillNormalizer()
    normalized = normalizer.normalize_list(raw_skills)

    analyzer = ResumeConfidenceAnalyzer()
    report = analyzer.analyze(parsed["raw_text"], parsed["sections"], normalized)

    if len(normalized) == 0:
        print("  [FAIL] No skills extracted from resume")
        return False

    if not (0 <= report.overall_quality_score <= 100):
        print("  [FAIL] Quality score out of range")
        return False

    print(
        f"  [PASS] Resume pipeline works: "
        f"{len(normalized)} skills, "
        f"quality={report.overall_quality_score:.1f}/100"
    )
    return True


def main() -> int:
    """Run all integration verifications."""
    print("=" * 65)
    print("  INTEGRATION VERIFICATION")
    print("=" * 65)
    print()

    checks = [
        verify_imports,
        verify_evaluation_pipeline,
        verify_skill_pipeline,
        verify_recommendation_pipeline,
        verify_database_pipeline,
        verify_resume_pipeline,
    ]

    results = [check() for check in checks]
    passed = sum(results)
    total = len(results)

    print()
    print("=" * 65)
    print(f"  Integration Verification: {passed}/{total} passed")
    print("=" * 65)

    if passed == total:
        print("  [PASS] All integrations verified. System is ready.")
        return 0
    else:
        print(f"  [FAIL] {total - passed} integration(s) failed. Fix before running.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
