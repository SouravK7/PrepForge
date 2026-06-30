"""
System health check.

Verifies all components are working correctly.
Run before starting the application or after any changes.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path


def check(name: str, fn) -> bool:
    """
    Run one health check.

    Args:
        name: Check name.
        fn: Callable that returns True/False or raises.

    Returns:
        True if passed.
    """
    start = time.time()
    try:
        result = fn()
        elapsed = (time.time() - start) * 1000
        if result is not False:
            print(f"  [PASS] {name:<45} {elapsed:>6.0f}ms")
            return True
        else:
            print(f"  [FAIL] {name:<45} FAILED")
            return False
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        print(f"  [FAIL] {name:<45} ERROR: {str(e)[:60]}")
        return False


def main() -> int:
    """Run all health checks."""
    print("=" * 65)
    print("  SYSTEM HEALTH CHECK")
    print("=" * 65)
    results = []

    # Config Layer
    print("\n  [Config]")

    def check_config():
        from ai_core.shared.config_loader import config
        return config.get("app_config", "app.name") == "AI Interview Assistant"

    results.append(check("Config loader", check_config))

    def check_yaml_files():
        import yaml
        for f in Path("configs").glob("*.yaml"):
            with open(f) as fh:
                yaml.safe_load(fh)
        return True

    results.append(check("YAML configs valid", check_yaml_files))

    # Data Layer
    print("\n  [Data]")

    def check_data_files():
        import json
        required = [
            "data/competencies/software_engineer.json",
            "data/questions/software_engineer.json",
            "data/rubrics/technical_rubrics.json",
            "data/resources/learning_resources.json",
            "data/benchmark/oop_benchmark_v1.json",
        ]
        for f in required:
            if not Path(f).exists():
                raise FileNotFoundError(f)
            with open(f) as fh:
                json.load(fh)
        return True

    results.append(check("Data files exist and valid", check_data_files))

    # Database Layer
    print("\n  [Database]")

    def check_database():
        from database.db_setup import health_check
        return health_check()

    results.append(check("Database connection", check_database))

    def check_tables():
        from database.db_setup import SessionLocal
        from database.models import User, InterviewSession, Answer
        session = SessionLocal()
        try:
            session.query(User).count()
            session.query(InterviewSession).count()
            session.query(Answer).count()
            return True
        finally:
            session.close()

    results.append(check("Database tables exist", check_tables))

    # AI Models
    print("\n  [AI Models]")

    def check_spacy():
        from ai_core.shared.model_manager import model_manager
        model = model_manager.get_spacy_model()
        return model is not None

    results.append(check("spaCy model loads", check_spacy))

    def check_embeddings():
        from ai_core.shared.model_manager import model_manager
        model = model_manager.get_embedding_model()
        return model is not None

    results.append(check("Sentence Transformer loads", check_embeddings))

    def check_embedding_output():
        from ai_core.shared.embedding_service import EmbeddingService
        emb = EmbeddingService.embed_text("test sentence")
        return len(emb) == 384

    results.append(check("Embedding generates 384-dim vector", check_embedding_output))

    # AI Pipelines
    print("\n  [AI Pipelines]")

    def check_evaluation_pipeline():
        from ai_core.evaluation_pipeline import EvaluationOrchestrator
        from schemas.answer_schema import AnswerInput
        from schemas.question_schema import QuestionType
        orchestrator = EvaluationOrchestrator()
        answer = AnswerInput(
            session_id=0, user_id=0,
            question_id="health_test", competency_id="comp_test",
            question_text="Explain OOP.", question_type=QuestionType.TECHNICAL,
            sample_answer="OOP has encapsulation and inheritance.",
            required_concepts=["encapsulation", "inheritance"],
            optional_concepts=[], rubric_id="rubric_technical_standard",
            user_answer="OOP involves encapsulation and inheritance of classes.",
        )
        result = orchestrator.evaluate(answer)
        return 0.0 <= result.scores.weighted_final <= 100.0

    results.append(check("Evaluation ensemble end-to-end", check_evaluation_pipeline))

    def check_skill_pipeline():
        from ai_core.skill_pipeline import CompetencyGraph, EloEstimator
        graph = CompetencyGraph()
        graph.load_role("software_engineer")
        elo = EloEstimator()
        expected = elo.compute_expected_score(1000.0, 1200.0)
        return graph.competency_count() > 0 and 0.0 < expected < 0.5

    results.append(check("Skill graph and Elo estimator", check_skill_pipeline))

    def check_recommendation_pipeline():
        from ai_core.recommendation_pipeline import ResourceMatcher
        matcher = ResourceMatcher()
        return matcher.resource_count() > 0

    results.append(check("Recommendation resource loader", check_recommendation_pipeline))

    def check_resume_pipeline():
        from ai_core.resume_pipeline import SkillExtractor, SkillNormalizer
        extractor = SkillExtractor()
        normalizer = SkillNormalizer()
        skills = extractor.extract("Python machine learning docker", "skills")
        normalized = normalizer.normalize_list(skills)
        return len(normalized) > 0

    results.append(check("Resume skill extraction", check_resume_pipeline))

    # Services
    print("\n  [Services]")

    def check_interview_service():
        from database.db_setup import SessionLocal
        from services.interview_service import InterviewService
        session = SessionLocal()
        try:
            svc = InterviewService(session)
            return svc is not None
        finally:
            session.close()

    results.append(check("InterviewService initializes", check_interview_service))

    def check_analytics_service():
        from database.db_setup import SessionLocal
        from services.analytics_service import AnalyticsService
        session = SessionLocal()
        try:
            svc = AnalyticsService(session)
            stats = svc.get_dashboard_stats(user_id=99999)
            return "overview" in stats
        finally:
            session.close()

    results.append(check("AnalyticsService returns empty dashboard", check_analytics_service))

    # Benchmark
    print("\n  [Benchmark]")

    def check_benchmark_metrics():
        from benchmark.metrics import BenchmarkMetrics
        human = [10.0, 50.0, 80.0, 95.0]
        ai = [15.0, 45.0, 75.0, 90.0]
        metrics = BenchmarkMetrics.all_metrics(human, ai)
        return metrics["pearson_r"] > 0.99

    results.append(check("Benchmark metrics compute correctly", check_benchmark_metrics))

    # API
    print("\n  [API]")

    def check_api_import():
        from api.main import app
        return app is not None

    results.append(check("FastAPI app imports without error", check_api_import))

    def check_frontend_import():
        from frontend.streamlit_app import main
        return main is not None

    results.append(check("Streamlit app imports without error", check_frontend_import))

    # Summary
    passed = sum(results)
    total = len(results)
    failed = total - passed

    print(f"\n{'='*65}")
    print(f"  Health Check Summary: {passed}/{total} passed", end="")
    if failed > 0:
        print(f" ({failed} failed)")
    else:
        print(" (all clear)")
    print('='*65)

    if passed == total:
        print("  [PASS] System is healthy and ready to run.")
    else:
        print("  [WARN] Some checks failed. Review errors above.")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
