"""
NLP skill extractor.

Uses spaCy NER, pattern matching, and keyword detection
to extract skills from resume text.
"""

from __future__ import annotations

import re

from ai_core.shared.model_manager import model_manager
from schemas.resume_schema import ExtractedSkill


class SkillExtractor:
    """
    Extracts technical and soft skills from resume text.

    Uses multiple strategies:
    1. Curated technical skill keyword matching
    2. spaCy Named Entity Recognition (ORG / PRODUCT)
    3. Pattern matching for compound skill names
    4. Section-aware extraction (skills section gets highest confidence)
    """

    # Comprehensive technical skill keywords
    TECHNICAL_SKILLS: frozenset[str] = frozenset({
        # Programming Languages
        "python", "java", "javascript", "typescript", "c++", "c#", "golang",
        "rust", "kotlin", "swift", "ruby", "php", "scala", "r", "matlab",
        "bash", "shell", "perl", "haskell",

        # Web Technologies
        "html", "css", "react", "angular", "vue", "nextjs", "nodejs",
        "express", "django", "flask", "fastapi", "spring", "laravel",
        "rest api", "graphql", "websocket", "jquery", "bootstrap",

        # Databases
        "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle",
        "sql server", "cassandra", "elasticsearch", "dynamodb", "firestore",
        "sql", "nosql", "database design", "orm",

        # Cloud and DevOps
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "ansible", "jenkins", "github actions", "ci/cd", "linux",
        "nginx", "apache", "heroku", "vercel",

        # AI and Data Science
        "machine learning", "deep learning", "neural network", "nlp",
        "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
        "pandas", "numpy", "matplotlib", "seaborn", "plotly",
        "jupyter", "hugging face", "transformers", "bert", "gpt",
        "opencv", "yolo", "lstm", "cnn", "rnn", "gan",

        # Data Engineering
        "spark", "hadoop", "kafka", "airflow", "dbt", "snowflake",
        "bigquery", "data warehouse", "etl", "data pipeline",

        # Tools and Practices
        "git", "github", "gitlab", "jira", "agile", "scrum",
        "unit testing", "tdd", "microservices", "api", "oauth", "jwt",

        # Mobile
        "android", "ios", "react native", "flutter",
    })

    # Soft skills
    SOFT_SKILLS: frozenset[str] = frozenset({
        "communication", "teamwork", "leadership", "problem solving",
        "critical thinking", "time management", "project management",
        "collaboration", "mentoring", "presentation",
    })

    # Compound patterns: "React.js", "Node.js", "scikit-learn"
    COMPOUND_PATTERNS: list[re.Pattern] = [
        re.compile(r"\b(react\.js|node\.js|vue\.js|next\.js|three\.js)\b", re.IGNORECASE),
        re.compile(r"\b(scikit[-\s]learn)\b", re.IGNORECASE),
        re.compile(r"\b(machine[-\s]learning)\b", re.IGNORECASE),
        re.compile(r"\b(deep[-\s]learning)\b", re.IGNORECASE),
        re.compile(
            r"\b(natural[-\s]language[-\s]processing|nlp)\b", re.IGNORECASE
        ),
        re.compile(r"\b(ci[-/]cd)\b", re.IGNORECASE),
        re.compile(r"\b(rest[-\s]?api)\b", re.IGNORECASE),
    ]

    # Confidence per section
    _SECTION_CONFIDENCE: dict[str, float] = {
        "skills": 0.95,
        "certifications": 0.90,
        "experience": 0.80,
        "projects": 0.80,
        "summary": 0.75,
        "education": 0.70,
        "other": 0.60,
    }

    def extract(
        self,
        text: str,
        source_section: str = "unknown",
    ) -> list[ExtractedSkill]:
        """
        Extract all skills from a text block.

        Args:
            text: Text to extract skills from.
            source_section: Which resume section this text is from.
                           'skills' section gets highest confidence.

        Returns:
            List of ExtractedSkill objects.
        """
        if not text or not text.strip():
            return []

        text_lower = text.lower()
        found: dict[str, ExtractedSkill] = {}

        self._extract_by_keywords(text_lower, source_section, found)
        self._extract_by_patterns(text, source_section, found)
        self._extract_by_ner(text, source_section, found)

        return list(found.values())

    def extract_from_sections(
        self,
        sections: dict[str, str],
    ) -> list[ExtractedSkill]:
        """
        Extract skills from all resume sections.

        Skills section gets the highest confidence multiplier.
        Deduplicates across sections, keeping the highest confidence.

        Args:
            sections: Dict of section_name to section_text.

        Returns:
            Deduplicated list of ExtractedSkill objects.
        """
        all_skills: dict[str, ExtractedSkill] = {}

        for section_name, section_text in sections.items():
            if not section_text:
                continue

            skills = self.extract(section_text, source_section=section_name)

            for skill in skills:
                key = skill.normalized.lower()
                if key not in all_skills:
                    all_skills[key] = skill
                elif skill.confidence > all_skills[key].confidence:
                    all_skills[key] = skill

        return list(all_skills.values())

    # ── Private strategies ─────────────────────────────────────

    def _extract_by_keywords(
        self,
        text_lower: str,
        source_section: str,
        found: dict[str, ExtractedSkill],
    ) -> None:
        """Match skills against curated keyword lists."""
        base_conf = self._SECTION_CONFIDENCE.get(source_section, 0.70)

        for skill in self.TECHNICAL_SKILLS:
            if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
                key = skill.lower()
                if key not in found:
                    found[key] = ExtractedSkill(
                        raw_text=skill,
                        normalized=self._to_display_name(skill),
                        confidence=base_conf,
                        source_section=source_section,
                    )

        for skill in self.SOFT_SKILLS:
            if skill in text_lower:
                key = skill.lower()
                if key not in found:
                    found[key] = ExtractedSkill(
                        raw_text=skill,
                        normalized=skill.title(),
                        confidence=base_conf * 0.8,
                        source_section=source_section,
                    )

    def _extract_by_patterns(
        self,
        text: str,
        source_section: str,
        found: dict[str, ExtractedSkill],
    ) -> None:
        """Match compound skill names via regex patterns."""
        for pattern in self.COMPOUND_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                raw = match[0] if isinstance(match, tuple) else match
                key = re.sub(r"[-.\s]", "", raw.lower())
                if key not in found:
                    found[key] = ExtractedSkill(
                        raw_text=raw,
                        normalized=self._normalize_compound(raw),
                        confidence=0.92,
                        source_section=source_section,
                    )

    def _extract_by_ner(
        self,
        text: str,
        source_section: str,
        found: dict[str, ExtractedSkill],
    ) -> None:
        """Use spaCy NER to detect technology entity mentions."""
        try:
            nlp = model_manager.get_spacy_model()
            doc = nlp(text[:5000])  # limit for performance

            for ent in doc.ents:
                if ent.label_ in ("ORG", "PRODUCT", "WORK_OF_ART"):
                    entity_text = ent.text.strip()
                    entity_lower = entity_text.lower()

                    # Only include plausible tech entity lengths
                    if entity_lower in self.TECHNICAL_SKILLS or len(entity_text) <= 20:
                        key = entity_lower
                        if key not in found:
                            found[key] = ExtractedSkill(
                                raw_text=entity_text,
                                normalized=entity_text,
                                confidence=0.70,
                                source_section=source_section,
                            )
        except Exception:
            # NER is a best-effort strategy; do not fail hard
            pass

    # ── Display name helpers ───────────────────────────────────

    _SPECIAL_CASES: dict[str, str] = {
        "python": "Python", "javascript": "JavaScript",
        "typescript": "TypeScript", "html": "HTML", "css": "CSS",
        "sql": "SQL", "nosql": "NoSQL", "aws": "AWS", "gcp": "GCP",
        "api": "API", "rest api": "REST API", "graphql": "GraphQL",
        "ci/cd": "CI/CD", "nlp": "NLP", "opencv": "OpenCV",
        "yolo": "YOLO", "lstm": "LSTM", "cnn": "CNN", "rnn": "RNN",
        "gan": "GAN", "bert": "BERT", "gpt": "GPT", "tdd": "TDD",
        "orm": "ORM", "jwt": "JWT", "etl": "ETL", "dbt": "dbt",
    }

    _COMPOUND_NORMS: dict[str, str] = {
        "react.js": "React.js", "node.js": "Node.js",
        "vue.js": "Vue.js", "next.js": "Next.js",
        "scikit-learn": "Scikit-learn", "scikit learn": "Scikit-learn",
        "machine-learning": "Machine Learning",
        "machine learning": "Machine Learning",
        "deep-learning": "Deep Learning", "deep learning": "Deep Learning",
        "natural language processing": "NLP",
        "natural-language-processing": "NLP",
        "ci/cd": "CI/CD", "ci-cd": "CI/CD",
        "rest api": "REST API", "rest-api": "REST API",
    }

    def _to_display_name(self, skill: str) -> str:
        """Convert skill keyword to proper display name."""
        return self._SPECIAL_CASES.get(skill.lower(), skill.title())

    def _normalize_compound(self, skill: str) -> str:
        """Normalize compound skill names to canonical form."""
        return self._COMPOUND_NORMS.get(skill.lower(), skill)
