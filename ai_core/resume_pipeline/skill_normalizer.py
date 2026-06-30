"""
Skill normalizer.

Normalizes skill name variations to canonical forms.
Example: "JS" -> "JavaScript", "ML" -> "Machine Learning"
"""

from __future__ import annotations

from schemas.resume_schema import ExtractedSkill


class SkillNormalizer:
    """
    Normalizes extracted skill names to canonical forms.

    Handles abbreviations, alternative spellings, and
    synonym mapping for consistent skill tracking.
    """

    # Abbreviation / synonym -> canonical name map
    NORMALIZATION_MAP: dict[str, str] = {
        # Programming languages
        "js": "JavaScript",
        "ts": "TypeScript",
        "py": "Python",
        "rb": "Ruby",
        "cpp": "C++",
        "c plus plus": "C++",
        "csharp": "C#",
        "c sharp": "C#",
        "golang": "Go",
        "go lang": "Go",

        # Web
        "reactjs": "React.js",
        "react js": "React.js",
        "react": "React.js",
        "nodejs": "Node.js",
        "node js": "Node.js",
        "node": "Node.js",
        "vuejs": "Vue.js",
        "vue js": "Vue.js",
        "nextjs": "Next.js",
        "next js": "Next.js",
        "expressjs": "Express.js",
        "express js": "Express.js",

        # Data Science and ML
        "ml": "Machine Learning",
        "dl": "Deep Learning",
        "ai": "Artificial Intelligence",
        "cv": "Computer Vision",
        "nlp": "NLP",
        "natural language processing": "NLP",
        "sklearn": "Scikit-learn",
        "scikit learn": "Scikit-learn",
        "tf": "TensorFlow",
        "tensorflow": "TensorFlow",
        "torch": "PyTorch",
        "hf": "Hugging Face",

        # Databases
        "pg": "PostgreSQL",
        "postgres": "PostgreSQL",
        "mysql": "MySQL",
        "mongo": "MongoDB",
        "mongodb": "MongoDB",
        "es": "Elasticsearch",

        # Cloud
        "aws": "AWS",
        "amazon web services": "AWS",
        "gcp": "GCP",
        "google cloud": "GCP",
        "google cloud platform": "GCP",
        "azure": "Microsoft Azure",
        "microsoft azure": "Microsoft Azure",

        # DevOps
        "k8s": "Kubernetes",
        "kube": "Kubernetes",
        "gh actions": "GitHub Actions",
        "github actions": "GitHub Actions",
        "gitlab ci": "GitLab CI/CD",
        "cicd": "CI/CD",
        "ci cd": "CI/CD",

        # Practices
        "tdd": "Test-Driven Development",
        "bdd": "Behavior-Driven Development",
        "oop": "Object-Oriented Programming",
        "fp": "Functional Programming",
        "rest": "REST API",
        "restful": "REST API",
        "rest api": "REST API",
        "graphql": "GraphQL",
        "gql": "GraphQL",

        # Tools
        "vscode": "VS Code",
        "vs code": "VS Code",
        "vim": "Vim",
        "pycharm": "PyCharm",
        "intellij": "IntelliJ IDEA",

        # Data tools
        "pd": "Pandas",
        "np": "NumPy",
        "mpl": "Matplotlib",
    }

    # Canonical skill names for exact reverse lookup
    CANONICAL_NAMES: frozenset[str] = frozenset({
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#",
        "Go", "Rust", "Ruby", "PHP", "Scala", "R",
        "React.js", "Node.js", "Vue.js", "Next.js", "Angular",
        "Django", "Flask", "FastAPI", "Express.js",
        "HTML", "CSS", "GraphQL", "REST API",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite",
        "AWS", "GCP", "Microsoft Azure", "Docker", "Kubernetes",
        "Git", "GitHub", "GitLab", "CI/CD",
        "Machine Learning", "Deep Learning", "NLP",
        "TensorFlow", "PyTorch", "Scikit-learn",
        "Pandas", "NumPy", "Matplotlib", "Plotly",
        "SQL", "NoSQL", "Elasticsearch",
        "Linux", "Bash", "Terraform", "Ansible",
    })

    def normalize(self, skill: ExtractedSkill) -> ExtractedSkill:
        """
        Normalize a single extracted skill to canonical form.

        Args:
            skill: ExtractedSkill to normalize.

        Returns:
            New ExtractedSkill with normalized name.
        """
        normalized_name = self._lookup_normalization(skill.raw_text)

        return ExtractedSkill(
            raw_text=skill.raw_text,
            normalized=normalized_name,
            competency_id=skill.competency_id,
            confidence=skill.confidence,
            source_section=skill.source_section,
        )

    def normalize_list(
        self,
        skills: list[ExtractedSkill],
    ) -> list[ExtractedSkill]:
        """
        Normalize a list of extracted skills, deduplicating after normalization.

        Args:
            skills: List of ExtractedSkill to normalize.

        Returns:
            Deduplicated list of normalized skills.
            When duplicates exist, the higher-confidence entry is kept.
        """
        normalized: dict[str, ExtractedSkill] = {}

        for skill in skills:
            norm_skill = self.normalize(skill)
            key = norm_skill.normalized.lower()

            if key not in normalized:
                normalized[key] = norm_skill
            elif norm_skill.confidence > normalized[key].confidence:
                normalized[key] = norm_skill

        return list(normalized.values())

    def normalize_text(self, text: str) -> str:
        """
        Normalize a raw skill text string to its canonical form.

        Args:
            text: Raw skill text (e.g. "JS", "nodejs").

        Returns:
            Canonical skill name (e.g. "JavaScript", "Node.js").
        """
        return self._lookup_normalization(text)

    def _lookup_normalization(self, raw: str) -> str:
        """
        Look up normalized form for a raw skill string.

        Priority:
        1. Exact match in normalization map.
        2. Exact canonical name match (case-insensitive).
        3. Title-cased fallback.

        Args:
            raw: Raw skill text.

        Returns:
            Canonical skill name.
        """
        raw_lower = raw.lower().strip()

        # 1. Direct lookup in map
        if raw_lower in self.NORMALIZATION_MAP:
            return self.NORMALIZATION_MAP[raw_lower]

        # 2. Check if already a canonical name
        for canonical in self.CANONICAL_NAMES:
            if raw_lower == canonical.lower():
                return canonical

        # 3. Title-case fallback
        return raw.strip().title()
