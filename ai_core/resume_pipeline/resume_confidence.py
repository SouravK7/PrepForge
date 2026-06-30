"""
Resume confidence analyzer.

Assesses resume quality and detects potential issues
like buzzword overuse, missing descriptions, and
skill claims without supporting evidence.
"""

from __future__ import annotations

import re

from schemas.resume_schema import ExtractedSkill, ResumeConfidenceReport


class ResumeConfidenceAnalyzer:
    """
    Analyzes resume quality and flags potential issues.

    Detects:
    - Generic buzzwords without substance
    - Skills claimed but not mentioned in experience or projects
    - Missing or very thin section descriptions
    - Lack of quantified achievements
    """

    # Buzzwords that inflate resumes without substance
    BUZZWORDS: list[str] = [
        "passionate", "motivated", "self-starter", "go-getter",
        "team player", "hardworking", "detail-oriented", "results-driven",
        "dynamic", "innovative", "synergy", "leverage", "paradigm",
        "guru", "ninja", "rockstar", "wizard", "expert in everything",
        "extensive experience", "proven track record", "fast learner",
        "quick learner", "excellent communication skills",
        "strong work ethic", "outside the box", "thought leader",
    ]

    # Concrete, evidence-suggesting patterns
    QUANTIFIED_PATTERNS: list[re.Pattern] = [
        re.compile(
            r"\b\d+\s*(%|percent|users|records|requests|api|ms|seconds|hours|days|weeks|months|years)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(increased|decreased|reduced|improved|optimized|achieved|delivered)\s+by\s+\d+",
            re.IGNORECASE,
        ),
        re.compile(r"\bbuilt\s+(a|an|the)\b", re.IGNORECASE),
        re.compile(r"\bdeployed\s+(to|on|using)\b", re.IGNORECASE),
        re.compile(r"\bintegrated\s+(with|into)\b", re.IGNORECASE),
    ]

    def analyze(
        self,
        raw_text: str,
        sections: dict[str, str],
        extracted_skills: list[ExtractedSkill],
    ) -> ResumeConfidenceReport:
        """
        Analyze resume quality and produce a confidence report.

        Args:
            raw_text: Full resume text.
            sections: Detected resume sections.
            extracted_skills: Skills found in the resume.

        Returns:
            ResumeConfidenceReport with quality score and issues.
        """
        raw_lower = raw_text.lower()

        flagged_buzzwords, buzzword_count = self._check_buzzwords(raw_lower)
        missing_descriptions = self._check_missing_descriptions(sections)
        skill_claim_gaps = self._check_skill_claim_gaps(
            extracted_skills, sections
        )
        quality_score = self._compute_quality_score(
            raw_text=raw_text,
            sections=sections,
            buzzword_count=buzzword_count,
            missing_descriptions=missing_descriptions,
            skill_claim_gaps=skill_claim_gaps,
        )
        recommendations = self._generate_recommendations(
            buzzword_count=buzzword_count,
            flagged_buzzwords=flagged_buzzwords,
            missing_descriptions=missing_descriptions,
            skill_claim_gaps=skill_claim_gaps,
            quality_score=quality_score,
        )

        return ResumeConfidenceReport(
            overall_quality_score=round(quality_score, 1),
            buzzword_count=buzzword_count,
            flagged_buzzwords=flagged_buzzwords,
            missing_descriptions=missing_descriptions,
            skill_claim_gaps=skill_claim_gaps,
            recommendations=recommendations,
        )

    # ── Detection helpers ──────────────────────────────────────

    def _check_buzzwords(
        self,
        text_lower: str,
    ) -> tuple[list[str], int]:
        """
        Detect generic buzzwords in resume text.

        Args:
            text_lower: Lowercase resume text.

        Returns:
            Tuple of (flagged_buzzwords_list, total_count).
        """
        found = [bw for bw in self.BUZZWORDS if bw in text_lower]
        return found, len(found)

    def _check_missing_descriptions(
        self,
        sections: dict[str, str],
    ) -> list[str]:
        """
        Identify sections that are too thin or absent.

        Args:
            sections: Resume sections dict.

        Returns:
            List of missing/thin section description strings.
        """
        missing = []

        experience_text = sections.get("experience", "")
        if experience_text and len(experience_text.split()) < 30:
            missing.append(
                "Experience section is very short. "
                "Add detailed descriptions of responsibilities and achievements."
            )

        projects_text = sections.get("projects", "")
        if projects_text and len(projects_text.split()) < 20:
            missing.append(
                "Projects section lacks detail. "
                "Describe the problem, solution, and technologies used."
            )

        summary_text = sections.get("summary", "")
        if not summary_text:
            missing.append(
                "No professional summary detected. "
                "Add a 2-3 sentence overview of your background and goals."
            )

        return missing

    def _check_skill_claim_gaps(
        self,
        skills: list[ExtractedSkill],
        sections: dict[str, str],
    ) -> list[str]:
        """
        Detect skills listed in the skills section but unsupported by experience.

        Args:
            skills: Extracted skills from resume.
            sections: Resume sections.

        Returns:
            List of potentially unsupported skill claim strings.
        """
        experience_text = (
            sections.get("experience", "")
            + " "
            + sections.get("projects", "")
        ).lower()

        gaps = []
        for skill in skills:
            if skill.source_section == "skills":
                skill_lower = skill.normalized.lower()
                if (
                    skill_lower not in experience_text
                    and skill.confidence >= 0.85
                ):
                    gaps.append(
                        f"'{skill.normalized}' is listed in skills "
                        f"but not mentioned in experience or projects."
                    )

        return gaps[:5]  # Cap at 5 to avoid noise

    def _compute_quality_score(
        self,
        raw_text: str,
        sections: dict[str, str],
        buzzword_count: int,
        missing_descriptions: list[str],
        skill_claim_gaps: list[str],
    ) -> float:
        """
        Compute overall resume quality score (0-100).

        Args:
            raw_text: Full resume text.
            sections: Detected sections.
            buzzword_count: Number of buzzwords found.
            missing_descriptions: Missing section issues.
            skill_claim_gaps: Skill claim gaps.

        Returns:
            Quality score 0.0-100.0.
        """
        score = 100.0

        # Penalize buzzwords (up to -20)
        score -= min(buzzword_count * 3, 20)

        # Penalize missing descriptions (up to -20)
        score -= min(len(missing_descriptions) * 7, 20)

        # Penalize skill claim gaps (up to -15)
        score -= min(len(skill_claim_gaps) * 5, 15)

        # Reward quantified achievements (up to +10)
        quantified_count = sum(
            1 for p in self.QUANTIFIED_PATTERNS if p.search(raw_text)
        )
        score += min(quantified_count * 2, 10)

        # Penalize very short resumes
        word_count = len(raw_text.split())
        if word_count < 150:
            score -= 20
        elif word_count < 250:
            score -= 10

        # Reward having multiple populated sections
        section_count = sum(1 for v in sections.values() if v)
        score += min(section_count * 2, 10)

        return float(max(0.0, min(100.0, score)))

    def _generate_recommendations(
        self,
        buzzword_count: int,
        flagged_buzzwords: list[str],
        missing_descriptions: list[str],
        skill_claim_gaps: list[str],
        quality_score: float,
    ) -> list[str]:
        """
        Generate specific resume improvement recommendations.

        Args:
            buzzword_count: Number of buzzwords found.
            flagged_buzzwords: Specific buzzwords detected.
            missing_descriptions: Thin/missing section issues.
            skill_claim_gaps: Unsupported skill claims.
            quality_score: Overall quality score.

        Returns:
            List of actionable recommendation strings.
        """
        recommendations: list[str] = []

        if buzzword_count >= 3:
            sample = ", ".join(flagged_buzzwords[:3])
            recommendations.append(
                f"Replace generic buzzwords ({sample}) "
                f"with specific achievements and measurable outcomes."
            )

        if missing_descriptions:
            recommendations.extend(missing_descriptions[:2])

        if skill_claim_gaps:
            recommendations.append(
                "Add project or experience entries that demonstrate "
                "the skills listed in your skills section."
            )

        if quality_score < 60:
            recommendations.append(
                "Consider adding quantified achievements "
                "(e.g., 'Reduced API response time by 40%') "
                "to strengthen your resume."
            )

        if not recommendations:
            recommendations.append(
                "Resume quality looks good. "
                "Tailor specific skills and achievements "
                "to the target job description."
            )

        return recommendations
