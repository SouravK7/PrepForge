"""
Complete project setup script.

Run this once after cloning to initialize everything.
Creates folders, downloads models, initializes database,
loads seed data, and verifies the system is ready.
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*65}")
    print(f"  {title}")
    print('='*65)


def print_step(step: str) -> None:
    """Print a step in progress."""
    print(f"  -> {step}...")


def print_ok(msg: str) -> None:
    """Print success message."""
    print(f"  [PASS] {msg}")


def print_fail(msg: str) -> None:
    """Print failure message."""
    print(f"  [FAIL] {msg}")


def create_directories() -> None:
    """Create all required directories."""
    print_header("Creating Directory Structure")

    dirs = [
        "ai_core/shared",
        "ai_core/evaluation_pipeline",
        "ai_core/skill_pipeline",
        "ai_core/recommendation_pipeline",
        "ai_core/resume_pipeline",
        "ai_core/question_pipeline",
        "schemas",
        "configs",
        "data/competencies",
        "data/questions",
        "data/rubrics",
        "data/resources",
        "data/benchmark",
        "database",
        "services",
        "api/routes",
        "api/middleware",
        "frontend/pages",
        "frontend/components",
        "benchmark/reports",
        "prompts/v1",
        "tests",
        "logs",
        "models/cache",
        "docs",
        "scripts",
        "uploads",
        ".streamlit",
    ]

    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

    print_ok(f"Created {len(dirs)} directories")


def create_init_files() -> None:
    """Create __init__.py for all Python packages."""
    print_header("Creating Package Init Files")

    packages = [
        "ai_core",
        "ai_core/shared",
        "ai_core/evaluation_pipeline",
        "ai_core/skill_pipeline",
        "ai_core/recommendation_pipeline",
        "ai_core/resume_pipeline",
        "ai_core/question_pipeline",
        "schemas",
        "database",
        "services",
        "api",
        "api/routes",
        "api/middleware",
        "frontend",
        "frontend/pages",
        "frontend/components",
        "benchmark",
        "tests",
    ]

    created = 0
    for package in packages:
        init_file = Path(package) / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Package initialization."""\n')
            created += 1

    print_ok(f"Created {created} __init__.py files")


def create_env_file() -> None:
    """Create .env file from template if not exists."""
    print_header("Environment Configuration")

    env_file = Path(".env")
    if env_file.exists():
        print_ok(".env file already exists")
        return

    env_example = Path(".env.example")
    if env_example.exists():
        env_file.write_text(env_example.read_text())
        print_ok("Created .env from .env.example")
    else:
        env_content = """APP_NAME=AI Interview Assistant
APP_VERSION=1.0.0
DEBUG=True
DATABASE_URL=sqlite:///interview_assistant.db
SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
OPENAI_API_KEY=optional
USE_LLM=False
LLM_PROVIDER=openai
EMBEDDING_MODEL=all-MiniLM-L6-v2
SPACY_MODEL=en_core_web_sm
LOG_LEVEL=INFO
LOG_FILE=logs/ai_decisions.log
DATA_VERSION=v1
BENCHMARK_VERSION=v1
MODEL_VERSION=1.0.0
"""
        env_file.write_text(env_content)
        print_ok("Created .env with default settings")


def download_nlp_models() -> None:
    """Download required NLP models."""
    print_header("Downloading NLP Models")

    # spaCy model
    print_step("Downloading spaCy en_core_web_sm")
    result = subprocess.run(
        [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print_ok("spaCy en_core_web_sm downloaded")
    else:
        print_fail(f"spaCy download failed: {result.stderr[:100]}")

    # NLTK data
    print_step("Downloading NLTK data packages")
    try:
        import nltk
        packages = [
            "punkt", "stopwords", "wordnet",
            "averaged_perceptron_tagger", "vader_lexicon",
        ]
        for pkg in packages:
            nltk.download(pkg, quiet=True)
        print_ok(f"NLTK packages downloaded: {', '.join(packages)}")
    except Exception as e:
        print_fail(f"NLTK download failed: {e}")


def initialize_database() -> None:
    """Initialize database and load seed data."""
    print_header("Database Initialization")

    try:
        print_step("Creating database tables")
        from database.db_setup import init_db
        init_db()
        print_ok("Database tables created")

        print_step("Loading seed data")
        from database.seed_data import run_seed
        run_seed()
        print_ok("Seed data loaded")

    except Exception as e:
        print_fail(f"Database init failed: {e}")
        raise


def validate_data_files() -> None:
    """Validate all JSON data files exist and are valid."""
    print_header("Validating Knowledge Assets")

    try:
        result = subprocess.run(
            [sys.executable, "scripts/load_data.py"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print_ok("All knowledge assets validated")
        else:
            print_fail("Data validation failed")
            print(result.stdout[-300:])
    except FileNotFoundError:
        # load_data.py may not exist yet
        import json
        data_files = [
            "data/competencies/software_engineer.json",
            "data/questions/software_engineer.json",
            "data/rubrics/technical_rubrics.json",
            "data/resources/learning_resources.json",
        ]
        all_valid = True
        for f in data_files:
            if Path(f).exists():
                try:
                    with open(f) as fh:
                        json.load(fh)
                    print_ok(f"Valid: {f}")
                except Exception as e:
                    print_fail(f"Invalid JSON: {f}: {e}")
                    all_valid = False
            else:
                print_fail(f"Missing: {f}")
                all_valid = False

        if all_valid:
            print_ok("All data files valid")


def run_quick_test() -> None:
    """Run a quick sanity test on the core pipeline."""
    print_header("Core Pipeline Sanity Check")

    try:
        print_step("Testing evaluation pipeline")
        from ai_core.evaluation_pipeline import EvaluationOrchestrator
        from schemas.answer_schema import AnswerInput
        from schemas.question_schema import QuestionType

        orchestrator = EvaluationOrchestrator()
        answer = AnswerInput(
            session_id=0,
            user_id=0,
            question_id="setup_test",
            competency_id="comp_se_oop",
            question_text="Explain OOP.",
            question_type=QuestionType.TECHNICAL,
            sample_answer="OOP has encapsulation, inheritance, polymorphism, abstraction.",
            required_concepts=["encapsulation", "inheritance", "polymorphism"],
            optional_concepts=[],
            rubric_id="rubric_technical_standard",
            user_answer=(
                "OOP has four pillars: Encapsulation, Inheritance, "
                "Polymorphism, and Abstraction."
            ),
        )
        result = orchestrator.evaluate(answer)
        score = result.scores.weighted_final
        print_ok(f"Evaluation pipeline works. Test score: {score:.1f}/100")

    except Exception as e:
        print_fail(f"Pipeline test failed: {e}")
        raise

    try:
        print_step("Testing skill pipeline")
        from ai_core.skill_pipeline import CompetencyGraph
        graph = CompetencyGraph()
        graph.load_role("software_engineer")
        count = graph.competency_count()
        print_ok(f"Skill graph loaded: {count} competencies")

    except Exception as e:
        print_fail(f"Skill pipeline test failed: {e}")

    try:
        print_step("Testing recommendation pipeline")
        from ai_core.recommendation_pipeline import ResourceMatcher
        matcher = ResourceMatcher()
        count = matcher.resource_count()
        print_ok(f"Resources loaded: {count} learning resources")

    except Exception as e:
        print_fail(f"Recommendation pipeline test failed: {e}")

    try:
        print_step("Testing resume pipeline")
        from ai_core.resume_pipeline import SkillExtractor
        extractor = SkillExtractor()
        skills = extractor.extract("Python machine learning docker REST API")
        print_ok(f"Resume skill extraction works: {len(skills)} skills found")

    except Exception as e:
        print_fail(f"Resume pipeline test failed: {e}")


def create_streamlit_config() -> None:
    """Create Streamlit configuration."""
    print_header("Streamlit Configuration")

    config_path = Path(".streamlit/config.toml")
    if not config_path.exists():
        config_path.parent.mkdir(exist_ok=True)
        config_path.write_text("""[theme]
primaryColor = "#3498db"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8f9fa"
textColor = "#2c3e50"
font = "sans serif"

[server]
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
""")
        print_ok("Streamlit config created")
    else:
        print_ok("Streamlit config already exists")


def print_final_instructions() -> None:
    """Print setup completion and next steps."""
    print_header("Setup Complete")

    print("""
  The project is ready. Start the system with:

  Terminal 1 - Start API backend:
    uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

  Terminal 2 - Start Streamlit frontend:
    streamlit run app.py

  Then open: http://localhost:8501

  Other useful commands:

    Run all tests:
      python scripts/run_all_tests.py

    Run validation:
      python scripts/run_full_validation.py

    Health check:
      python scripts/health_check.py

    Demo run:
      python scripts/run_demo.py

    API docs:
      http://127.0.0.1:8000/docs
""")


def main() -> None:
    """Run complete project setup."""
    print_header("AI Interview Assistant - Project Setup")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Directory: {Path.cwd()}")

    create_directories()
    create_init_files()
    create_env_file()
    download_nlp_models()
    initialize_database()
    validate_data_files()
    run_quick_test()
    create_streamlit_config()
    print_final_instructions()


if __name__ == "__main__":
    main()
