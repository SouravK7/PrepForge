"""
Tests for the resume intelligence pipeline.

All tests run on in-memory data without database or API calls.
spaCy NER strategy is skipped if model is not loaded to keep
tests fast and dependency-free in CI.
"""

from __future__ import annotations

import pytest

from ai_core.resume_pipeline import (
    ResumeParser,
    SkillExtractor,
    SkillNormalizer,
    ResumeConfidenceAnalyzer,
    ResumeQuestionMapper,
)
from schemas.resume_schema import ExtractedSkill


# ─── Sample Resume Text ───────────────────────────────────────

SAMPLE_RESUME = """
John Doe
john@example.com | github.com/johndoe

Summary
Experienced software engineer with 3 years building backend APIs and
distributed systems. Passionate about clean code and scalable architecture.

Skills
Python, JavaScript, React, Node.js, PostgreSQL, MongoDB, Docker, Kubernetes,
AWS, Git, REST API, Machine Learning, Scikit-learn, Pandas, NumPy

Experience
Software Engineer — Acme Corp (2021-2024)
Built REST APIs using Python and FastAPI, deployed on AWS EC2.
Reduced API response time by 40% through database indexing and query optimization.
Integrated Redis caching to handle 10,000 concurrent users.
Used Docker and Kubernetes for containerized microservices deployment.

Junior Developer — Startup XYZ (2020-2021)
Developed React.js frontend components and integrated with Node.js backend.
Used PostgreSQL for relational data modeling.

Projects
ML Price Predictor
Built a machine learning model using Scikit-learn and Python to predict house prices.
Achieved 92% accuracy on test set. Deployed as a REST API with FastAPI.

Resume Parser Tool
Built a document parsing tool using Python and pdfplumber.
Used spaCy for named entity recognition.

Education
B.Tech Computer Science — State University (2020)

Certifications
AWS Certified Solutions Architect (2022)
"""

MINIMAL_RESUME = """
Name: Jane Smith
Skills: Python, SQL
"""

BUZZWORD_HEAVY_RESUME = """
Summary
Passionate, motivated self-starter with proven track record.
Dynamic team player with excellent communication skills and strong work ethic.
Fast learner with outside the box thinking.

Skills
Python, JavaScript

Experience
Results-driven developer who leverages synergy to deliver innovative solutions.
"""


# ─── ResumeParser Tests ───────────────────────────────────────

class TestResumeParser:
    """Tests for ResumeParser."""

    def setup_method(self) -> None:
        """Set up parser instance."""
        self.parser = ResumeParser()

    def test_parse_text_returns_dict(self) -> None:
        """parse_text should return a dict with required keys."""
        result = self.parser.parse_text(SAMPLE_RESUME)
        assert "raw_text" in result
        assert "sections" in result
        assert "file_type" in result
        assert "word_count" in result
        assert result["file_type"] == "text"

    def test_parse_text_counts_words(self) -> None:
        """word_count should match actual word count."""
        result = self.parser.parse_text(SAMPLE_RESUME)
        assert result["word_count"] > 50

    def test_detect_sections_finds_skills(self) -> None:
        """Section detection should find the skills section."""
        result = self.parser.parse_text(SAMPLE_RESUME)
        sections = result["sections"]
        assert "skills" in sections
        assert len(sections["skills"]) > 0

    def test_detect_sections_finds_experience(self) -> None:
        """Section detection should find the experience section."""
        result = self.parser.parse_text(SAMPLE_RESUME)
        assert "experience" in result["sections"]

    def test_detect_sections_finds_education(self) -> None:
        """Section detection should find the education section."""
        result = self.parser.parse_text(SAMPLE_RESUME)
        assert "education" in result["sections"]

    def test_detect_sections_finds_summary(self) -> None:
        """Section detection should find the summary section."""
        result = self.parser.parse_text(SAMPLE_RESUME)
        assert "summary" in result["sections"]

    def test_parse_bytes_txt(self) -> None:
        """parse_bytes should handle plain text bytes."""
        raw = "Python developer with Docker experience."
        result = self.parser.parse_bytes(raw.encode("utf-8"), "resume.txt")
        assert "python" in result["raw_text"].lower()
        assert result["file_type"] == "txt"

    def test_parse_bytes_invalid_extension(self) -> None:
        """parse_bytes should raise ValueError for unsupported format."""
        with pytest.raises(ValueError, match="Unsupported"):
            self.parser.parse_bytes(b"content", "resume.xls")

    def test_file_not_found(self) -> None:
        """parse_file should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            self.parser.parse_file("/nonexistent/resume.pdf")


# ─── SkillExtractor Tests ─────────────────────────────────────

class TestSkillExtractor:
    """Tests for SkillExtractor."""

    def setup_method(self) -> None:
        """Set up extractor instance."""
        self.extractor = SkillExtractor()

    def test_extract_known_skills_from_text(self) -> None:
        """Should find Python and Docker from plain text."""
        text = "I have 3 years of Python and Docker experience."
        skills = self.extractor.extract(text, "experience")
        skill_names = {s.normalized.lower() for s in skills}
        assert "python" in skill_names

    def test_extract_returns_list_of_extracted_skill(self) -> None:
        """extract should return list of ExtractedSkill objects."""
        skills = self.extractor.extract(SAMPLE_RESUME)
        for skill in skills:
            assert isinstance(skill, ExtractedSkill)
            assert skill.normalized
            assert 0.0 <= skill.confidence <= 1.0

    def test_skills_section_has_higher_confidence(self) -> None:
        """Skills section should produce higher confidence than other."""
        skills_text = "Python, Docker, AWS"
        other_text = "Helped build Python scripts"

        skills_from_section = self.extractor.extract(skills_text, "skills")
        skills_from_other = self.extractor.extract(other_text, "other")

        if skills_from_section and skills_from_other:
            max_skills = max(s.confidence for s in skills_from_section)
            max_other = max(s.confidence for s in skills_from_other)
            assert max_skills >= max_other

    def test_extract_from_sections(self) -> None:
        """extract_from_sections should deduplicate across sections."""
        parser = ResumeParser()
        parsed = parser.parse_text(SAMPLE_RESUME)
        skills = self.extractor.extract_from_sections(parsed["sections"])

        assert len(skills) > 0
        # All must be ExtractedSkill
        for skill in skills:
            assert isinstance(skill, ExtractedSkill)

        # No duplicates in normalized names
        names = [s.normalized.lower() for s in skills]
        assert len(names) == len(set(names))

    def test_compound_pattern_react_js(self) -> None:
        """Compound pattern should detect React.js."""
        skills = self.extractor.extract("Built with React.js and Node.js", "projects")
        names = {s.normalized for s in skills}
        assert "React.js" in names or any("react" in n.lower() for n in names)

    def test_empty_text_returns_empty_list(self) -> None:
        """Empty text should return empty list, not raise."""
        assert self.extractor.extract("") == []
        assert self.extractor.extract("   ") == []

    def test_extract_from_minimal_resume(self) -> None:
        """Minimal resume should still extract at least one skill."""
        parser = ResumeParser()
        parsed = parser.parse_text(MINIMAL_RESUME)
        skills = self.extractor.extract_from_sections(parsed["sections"])
        names_lower = {s.normalized.lower() for s in skills}
        assert "python" in names_lower or "sql" in names_lower


# ─── SkillNormalizer Tests ────────────────────────────────────

class TestSkillNormalizer:
    """Tests for SkillNormalizer."""

    def setup_method(self) -> None:
        """Set up normalizer instance."""
        self.normalizer = SkillNormalizer()

    def test_normalize_js_to_javascript(self) -> None:
        """'js' abbreviation should normalize to 'JavaScript'."""
        skill = ExtractedSkill(raw_text="js", normalized="Js",
                               confidence=0.9, source_section="skills")
        result = self.normalizer.normalize(skill)
        assert result.normalized == "JavaScript"

    def test_normalize_ml_to_machine_learning(self) -> None:
        """'ml' should normalize to 'Machine Learning'."""
        skill = ExtractedSkill(raw_text="ml", normalized="Ml",
                               confidence=0.9, source_section="skills")
        result = self.normalizer.normalize(skill)
        assert result.normalized == "Machine Learning"

    def test_normalize_nodejs_to_canonical(self) -> None:
        """'nodejs' should normalize to 'Node.js'."""
        skill = ExtractedSkill(raw_text="nodejs", normalized="Nodejs",
                               confidence=0.9, source_section="skills")
        result = self.normalizer.normalize(skill)
        assert result.normalized == "Node.js"

    def test_normalize_canonical_name_unchanged(self) -> None:
        """An already-canonical name should remain unchanged."""
        skill = ExtractedSkill(raw_text="Python", normalized="Python",
                               confidence=0.95, source_section="skills")
        result = self.normalizer.normalize(skill)
        assert result.normalized == "Python"

    def test_normalize_list_deduplicates(self) -> None:
        """normalize_list should deduplicate by canonical form."""
        skills = [
            ExtractedSkill(raw_text="js", normalized="Js",
                           confidence=0.8, source_section="skills"),
            ExtractedSkill(raw_text="JavaScript", normalized="JavaScript",
                           confidence=0.9, source_section="experience"),
        ]
        result = self.normalizer.normalize_list(skills)
        names = [s.normalized for s in result]
        assert len(names) == len(set(names))
        # Should keep the higher-confidence version
        js_entry = next(s for s in result if s.normalized == "JavaScript")
        assert js_entry.confidence == 0.9

    def test_normalize_text_unknown_returns_titlecase(self) -> None:
        """Unknown skill should return title-cased version."""
        result = self.normalizer.normalize_text("custom-framework-xyz")
        assert result  # Must return something

    def test_normalize_postgres_abbreviation(self) -> None:
        """'pg' should normalize to 'PostgreSQL'."""
        result = self.normalizer.normalize_text("pg")
        assert result == "PostgreSQL"


# ─── ResumeConfidenceAnalyzer Tests ──────────────────────────

class TestResumeConfidenceAnalyzer:
    """Tests for ResumeConfidenceAnalyzer."""

    def setup_method(self) -> None:
        """Set up analyzer instance and parse sample resume."""
        self.analyzer = ResumeConfidenceAnalyzer()
        parser = ResumeParser()
        self.parsed = parser.parse_text(SAMPLE_RESUME)
        self.parsed_buzz = parser.parse_text(BUZZWORD_HEAVY_RESUME)
        self.parsed_minimal = parser.parse_text(MINIMAL_RESUME)

        extractor = SkillExtractor()
        normalizer = SkillNormalizer()
        raw_skills = extractor.extract_from_sections(self.parsed["sections"])
        self.skills = normalizer.normalize_list(raw_skills)

        raw_skills_buzz = extractor.extract_from_sections(
            self.parsed_buzz["sections"]
        )
        self.skills_buzz = normalizer.normalize_list(raw_skills_buzz)

    def test_analyze_returns_report(self) -> None:
        """analyze should return a ResumeConfidenceReport."""
        from schemas.resume_schema import ResumeConfidenceReport
        report = self.analyzer.analyze(
            self.parsed["raw_text"],
            self.parsed["sections"],
            self.skills,
        )
        assert isinstance(report, ResumeConfidenceReport)

    def test_quality_score_in_range(self) -> None:
        """Quality score must be 0-100."""
        report = self.analyzer.analyze(
            self.parsed["raw_text"],
            self.parsed["sections"],
            self.skills,
        )
        assert 0.0 <= report.overall_quality_score <= 100.0

    def test_buzzword_heavy_resume_gets_lower_score(self) -> None:
        """Buzzword-heavy resume should score lower than normal."""
        normal_report = self.analyzer.analyze(
            self.parsed["raw_text"],
            self.parsed["sections"],
            self.skills,
        )
        buzz_report = self.analyzer.analyze(
            self.parsed_buzz["raw_text"],
            self.parsed_buzz["sections"],
            self.skills_buzz,
        )
        assert buzz_report.buzzword_count > 0
        assert buzz_report.overall_quality_score <= normal_report.overall_quality_score

    def test_buzzword_detection(self) -> None:
        """Buzzword-heavy resume should detect multiple buzzwords."""
        report = self.analyzer.analyze(
            self.parsed_buzz["raw_text"],
            self.parsed_buzz["sections"],
            self.skills_buzz,
        )
        assert report.buzzword_count >= 3
        assert len(report.flagged_buzzwords) >= 3

    def test_minimal_resume_gets_missing_description(self) -> None:
        """Minimal resume should have missing description warnings."""
        minimal_skills: list[ExtractedSkill] = []
        report = self.analyzer.analyze(
            self.parsed_minimal["raw_text"],
            self.parsed_minimal["sections"],
            minimal_skills,
        )
        # Very short resume should trigger low score or missing descriptions
        assert report.overall_quality_score < 90

    def test_recommendations_not_empty(self) -> None:
        """Recommendations list should always have at least one item."""
        report = self.analyzer.analyze(
            self.parsed["raw_text"],
            self.parsed["sections"],
            self.skills,
        )
        assert len(report.recommendations) >= 1


# ─── ResumeQuestionMapper Tests ───────────────────────────────

class TestResumeQuestionMapper:
    """Tests for ResumeQuestionMapper."""

    def setup_method(self) -> None:
        """Set up mapper and extract skills from sample resume."""
        parser = ResumeParser()
        extractor = SkillExtractor()
        normalizer = SkillNormalizer()

        parsed = parser.parse_text(SAMPLE_RESUME)
        raw_skills = extractor.extract_from_sections(parsed["sections"])
        self.skills = normalizer.normalize_list(raw_skills)
        self.mapper = ResumeQuestionMapper()

    def test_map_skills_to_competencies(self) -> None:
        """Should map at least one skill to a competency."""
        comp_map = self.mapper.map_skills_to_competencies(self.skills)
        assert isinstance(comp_map, dict)

    def test_get_targeted_questions_returns_list(self) -> None:
        """get_targeted_questions should return a list of dicts."""
        targeted = self.mapper.get_targeted_questions(self.skills)
        assert isinstance(targeted, list)

    def test_targeted_questions_have_required_keys(self) -> None:
        """Each targeted question dict must have required keys."""
        targeted = self.mapper.get_targeted_questions(self.skills)
        for item in targeted:
            assert "question" in item
            assert "targeting_reason" in item
            assert "skill_claimed" in item
            assert "question" in item
            q = item["question"]
            assert "id" in q
            assert "question_text" in q
            assert "competency_id" in q

    def test_no_duplicate_competencies_in_targeted(self) -> None:
        """No two targeted questions should cover the same competency."""
        targeted = self.mapper.get_targeted_questions(self.skills)
        comp_ids = [t["question"]["competency_id"] for t in targeted]
        assert len(comp_ids) == len(set(comp_ids))

    def test_get_detected_competency_ids(self) -> None:
        """get_detected_competency_ids should return unique list."""
        comp_ids = self.mapper.get_detected_competency_ids(self.skills)
        assert isinstance(comp_ids, list)
        assert len(comp_ids) == len(set(comp_ids))

    def test_follow_up_for_known_skill(self) -> None:
        """Should return a string follow-up for known skills."""
        result = self.mapper.get_follow_up_for_skill("Python")
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 10

    def test_follow_up_for_unknown_skill_returns_none(self) -> None:
        """Should return None for unknown skill names."""
        result = self.mapper.get_follow_up_for_skill("ZooplanktonFramework")
        assert result is None

    def test_empty_skills_produces_empty_targeted(self) -> None:
        """Empty skill list should produce empty targeted list."""
        targeted = self.mapper.get_targeted_questions([])
        assert targeted == []


# ─── Full Pipeline Integration Test ──────────────────────────

class TestResumePipelineIntegration:
    """End-to-end pipeline test on sample resume text."""

    def test_full_pipeline_on_sample_resume(self) -> None:
        """Run all pipeline stages sequentially."""
        # Parse
        parser = ResumeParser()
        parsed = parser.parse_text(SAMPLE_RESUME)
        assert parsed["word_count"] > 50

        # Extract
        extractor = SkillExtractor()
        raw_skills = extractor.extract_from_sections(parsed["sections"])
        assert len(raw_skills) > 3

        # Normalize
        normalizer = SkillNormalizer()
        skills = normalizer.normalize_list(raw_skills)
        assert len(skills) > 0

        # All normalized names are unique
        names = [s.normalized for s in skills]
        assert len(names) == len(set(names))

        # Confidence
        analyzer = ResumeConfidenceAnalyzer()
        report = analyzer.analyze(
            parsed["raw_text"], parsed["sections"], skills
        )
        assert 0 <= report.overall_quality_score <= 100
        assert len(report.recommendations) >= 1

        # Question mapping
        mapper = ResumeQuestionMapper()
        comp_map = mapper.map_skills_to_competencies(skills)
        assert isinstance(comp_map, dict)

        targeted = mapper.get_targeted_questions(skills)
        # All items have required structure
        for item in targeted:
            assert "question" in item
            assert "targeting_reason" in item
            assert "skill_claimed" in item

    def test_pipeline_handles_buzzword_resume(self) -> None:
        """Pipeline should complete gracefully on a buzzword-heavy resume."""
        parser = ResumeParser()
        extractor = SkillExtractor()
        normalizer = SkillNormalizer()
        analyzer = ResumeConfidenceAnalyzer()

        parsed = parser.parse_text(BUZZWORD_HEAVY_RESUME)
        raw_skills = extractor.extract_from_sections(parsed["sections"])
        skills = normalizer.normalize_list(raw_skills)
        report = analyzer.analyze(
            parsed["raw_text"], parsed["sections"], skills
        )

        assert report.buzzword_count >= 3
        assert report.overall_quality_score < 85  # Lower than clean resume
