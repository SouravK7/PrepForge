# AI Interview Assistant - Makefile
# Provides shortcuts for common development tasks.

.PHONY: setup test demo health validate clean run-api run-ui run-all

# -- Setup -----------------------------------------------------

setup:
	pip install -r requirements.txt
	python scripts/setup_project.py

models:
	python -m spacy download en_core_web_sm
	python -c "import nltk; [nltk.download(p, quiet=True) for p in ['punkt','stopwords','wordnet','averaged_perceptron_tagger','vader_lexicon']]"

db:
	python -c "from database.db_setup import init_db; init_db()"
	python database/seed_data.py

# -- Testing ---------------------------------------------------

test:
	python -m pytest tests/ -v --tb=short

test-fast:
	python -m pytest tests/ -x --tb=short -q

test-schemas:
	python -m pytest tests/test_schemas.py -v

test-eval:
	python -m pytest tests/test_evaluation_ensemble.py -v

test-skill:
	python -m pytest tests/test_skill_pipeline.py -v

test-api:
	python -m pytest tests/test_api.py -v

test-all:
	python scripts/run_all_tests.py

# -- Validation ------------------------------------------------

validate:
	python scripts/run_full_validation.py

benchmark:
	python -c "from benchmark.run_benchmark import BenchmarkRunner; BenchmarkRunner().run_all()"

ablation:
	python -c "from benchmark.ablation_runner import AblationRunner; AblationRunner().run('oop_benchmark_v1')"

# -- Health and Demo -------------------------------------------

health:
	python scripts/health_check.py

verify:
	python scripts/verify_integration.py

demo:
	python scripts/run_demo.py

# -- Running ---------------------------------------------------

run-api:
	uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

run-ui:
	streamlit run app.py

# -- Reports ---------------------------------------------------

report:
	python scripts/generate_final_report.py

# -- Cleanup ---------------------------------------------------

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -f logs/*.log
