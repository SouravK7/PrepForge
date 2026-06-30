"""
Integration script for the resume intelligence pipeline.

Runs the full pipeline on a sample resume and prints a detailed
report to stdout. Use this to verify the pipeline end-to-end
before wiring to database or API layers.

Usage:
    python scripts/test_resume_pipeline_integration.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_core.resume_pipeline import (
    ResumeParser,
    SkillExtractor,
    SkillNormalizer,
    ResumeConfidenceAnalyzer,
    ResumeQuestionMapper,
)


SAMPLE_RESUME = """
Jane Smith
jane@example.com | linkedin.com/in/janesmith | github.com/janesmith

Summary
Backend software engineer with 4 years of experience building scalable
APIs and data pipelines using Python, Django, and PostgreSQL.
Passionate about clean architecture and test-driven development.

Skills
Python, Django, FastAPI, PostgreSQL, Redis, Docker, AWS, Git,
REST API, Pandas, NumPy, Machine Learning, Scikit-learn, SQL, GitHub Actions

Experience
Senior Backend Engineer - TechCorp (2022-2024)
Designed and implemented REST APIs serving 50,000 daily active users.
Reduced database query time by 60% through PostgreSQL index optimization.
Migrated monolith to microservices architecture using Docker and AWS ECS.
Integrated Redis caching layer, reducing API response times from 800ms to 120ms.
Led a team of 4 engineers using Agile/Scrum methodology.

Backend Engineer - StartupABC (2020-2022)
Built data pipelines with Python and Pandas to process 2M records daily.
Implemented JWT-based authentication and role-based access control.
Deployed services on AWS EC2 with CI/CD via GitHub Actions.

Projects
Resume Intelligence System (2024)
Built a resume parsing and skill extraction tool using Python, pdfplumber, and spaCy.
Achieved 89% precision on skill detection benchmark.
Used machine learning classification to map skills to job competencies.

Price Forecast API
Trained a Scikit-learn gradient boosting model to predict product prices.
Deployed as REST API with FastAPI, achieving p99 latency of 45ms.

Education
B.Tech Computer Science - National University (2020)

Certifications
AWS Certified Developer - Associate (2022)
Google Professional Data Engineer (2023)
"""


def _print_section(title: str, content: str = "", width: int = 60) -> None:
    """Print a formatted section header."""
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)
    if content:
        print(content)


def run_pipeline(resume_text: str) -> None:
    """
    Run the full resume intelligence pipeline on given text.

    Args:
        resume_text: Raw resume text to process.
    """

    # ── Stage 1: Parse ─────────────────────────────────────────
    _print_section("Stage 1: Resume Parser")
    parser = ResumeParser()
    parsed = parser.parse_text(resume_text)

    print(f"  Words: {parsed['word_count']}")
    print(f"  Characters: {parsed['char_count']}")
    print(f"  Sections detected: {list(parsed['sections'].keys())}")

    for section_name, section_text in parsed["sections"].items():
        word_count = len(section_text.split())
        print(f"    - {section_name}: {word_count} words")

    # ── Stage 2: Skill Extraction ──────────────────────────────
    _print_section("Stage 2: Skill Extractor")
    extractor = SkillExtractor()
    raw_skills = extractor.extract_from_sections(parsed["sections"])

    print(f"  Raw skills detected: {len(raw_skills)}")
    for skill in sorted(raw_skills, key=lambda s: s.confidence, reverse=True)[:10]:
        print(
            f"    [{skill.confidence:.2f}] {skill.normalized} "
            f"(from: {skill.source_section})"
        )

    # ── Stage 3: Normalization ─────────────────────────────────
    _print_section("Stage 3: Skill Normalizer")
    normalizer = SkillNormalizer()
    skills = normalizer.normalize_list(raw_skills)

    print(f"  Normalized skills (deduplicated): {len(skills)}")
    for skill in sorted(skills, key=lambda s: s.confidence, reverse=True):
        print(f"    [{skill.confidence:.2f}] {skill.normalized}")

    # ── Stage 4: Confidence Analysis ──────────────────────────
    _print_section("Stage 4: Resume Confidence Analyzer")
    analyzer = ResumeConfidenceAnalyzer()
    report = analyzer.analyze(
        raw_text=parsed["raw_text"],
        sections=parsed["sections"],
        extracted_skills=skills,
    )

    print(f"  Overall Quality Score: {report.overall_quality_score:.1f} / 100")
    print(f"  Buzzwords detected: {report.buzzword_count}")
    if report.flagged_buzzwords:
        print(f"  Flagged: {', '.join(report.flagged_buzzwords[:5])}")
    if report.missing_descriptions:
        print("  Missing descriptions:")
        for m in report.missing_descriptions:
            print(f"    - {m}")
    if report.skill_claim_gaps:
        print("  Skill claim gaps:")
        for g in report.skill_claim_gaps:
            print(f"    - {g}")
    print("  Recommendations:")
    for rec in report.recommendations:
        print(f"    * {rec}")

    # ── Stage 5: Question Mapping ──────────────────────────────
    _print_section("Stage 5: Resume Question Mapper")
    mapper = ResumeQuestionMapper()

    comp_map = mapper.map_skills_to_competencies(skills)
    print(f"  Competencies matched: {len(comp_map)}")
    for comp_id, skill_names in comp_map.items():
        print(f"    {comp_id}: {', '.join(skill_names)}")

    print()
    targeted = mapper.get_targeted_questions(
        skills,
        difficulty=None,  # type: ignore[arg-type]
    )

    if targeted:
        print(f"  Targeted questions ({len(targeted)}):")
        for item in targeted:
            q = item["question"]
            print(f"    [{item['skill_claimed']}] {q['question_text'][:80]}...")
            print(f"      Reason: {item['targeting_reason'][:80]}...")
    else:
        print("  No targeted questions generated (questions bank may not be loaded)")

    # ── Summary ────────────────────────────────────────────────
    _print_section("Pipeline Summary")
    print(f"  Raw skills extracted:     {len(raw_skills)}")
    print(f"  Normalized skills:        {len(skills)}")
    print(f"  Competencies mapped:      {len(comp_map)}")
    print(f"  Targeted questions:       {len(targeted)}")
    print(f"  Quality score:            {report.overall_quality_score:.1f}")
    print(f"  Resume status: ", end="")

    if report.overall_quality_score >= 80:
        print("STRONG")
    elif report.overall_quality_score >= 60:
        print("AVERAGE")
    else:
        print("NEEDS IMPROVEMENT")


if __name__ == "__main__":
    print("Resume Intelligence Pipeline - Integration Test")
    print("Running on sample software engineer resume...")
    run_pipeline(SAMPLE_RESUME)
    print("\nDone.")
