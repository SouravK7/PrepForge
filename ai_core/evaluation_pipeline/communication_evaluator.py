"""
Communication evaluator.

Measures grammar quality, clarity, sentence structure,
and appropriate use of technical terminology.
"""

from __future__ import annotations

from ai_core.evaluation_pipeline.base_evaluator import BaseEvaluator, DimensionScore
from ai_core.shared.model_manager import model_manager
from ai_core.shared.text_processor import TextProcessor
from schemas.answer_schema import AnswerInput


class CommunicationEvaluator(BaseEvaluator):
    """
    Evaluates communication quality of the user's answer.

    Checks grammar, sentence structure, fluency, length,
    and appropriate use of technical vocabulary.
    Uses spaCy for linguistic analysis.
    """

    # Words indicating structured, clear communication
    STRUCTURE_INDICATORS = [
        "first", "second", "third", "finally", "additionally",
        "furthermore", "however", "therefore", "for example",
        "for instance", "in conclusion", "in summary", "specifically",
        "importantly", "because", "which means", "this means",
    ]

    # Generic filler phrases that reduce answer quality
    FILLER_PHRASES = [
        "basically", "like i said", "you know", "sort of",
        "kind of", "i think maybe", "i guess", "stuff like that",
        "and things", "etc etc",
    ]

    @property
    def dimension_name(self) -> str:
        """Dimension name for this evaluator."""
        return "communication"

    def evaluate(self, answer_input: AnswerInput) -> DimensionScore:
        """
        Evaluate communication quality of the answer.

        Args:
            answer_input: Contains user_answer.

        Returns:
            DimensionScore with communication quality score.
        """
        user_answer = answer_input.user_answer.strip()
        nlp = model_manager.get_spacy_model()
        doc = nlp(user_answer)

        # --- Component 1: Length appropriateness (0-25) ---
        word_count = TextProcessor.word_count(user_answer)
        length_score = self._score_length(word_count)

        # --- Component 2: Sentence structure (0-25) ---
        sentences = list(doc.sents)
        structure_score = self._score_structure(sentences)

        # --- Component 3: Structure indicators (0-25) ---
        indicator_score = self._score_indicators(user_answer.lower())

        # --- Component 4: Grammar quality (0-25) ---
        grammar_score = self._score_grammar(doc)

        # Total
        total_score = length_score + structure_score + indicator_score + grammar_score
        score = self._clamp(total_score)

        # Filler penalty
        filler_count = sum(
            1 for phrase in self.FILLER_PHRASES
            if phrase in user_answer.lower()
        )
        if filler_count > 0:
            penalty = min(filler_count * 3.0, 10.0)
            score = self._clamp(score - penalty)

        grammar_issues = self._detect_issues(doc, user_answer)
        reason, evidence = self._build_explanation(
            score=score,
            word_count=word_count,
            sentence_count=len(sentences),
            grammar_issues=grammar_issues,
        )

        return DimensionScore(
            score=round(score, 2),
            label="Communication Quality",
            reason=reason,
            evidence=evidence,
        )

    def _score_length(self, word_count: int) -> float:
        """
        Score answer length appropriateness.

        Args:
            word_count: Number of words in answer.

        Returns:
            Length score 0-25.
        """
        if word_count < 10:
            return 5.0
        elif word_count < 20:
            return 12.0
        elif word_count <= 100:
            # Sweet spot: full 25 points
            return 25.0
        elif word_count <= 200:
            return 22.0
        elif word_count <= 300:
            return 18.0
        else:
            # Too long: may be rambling
            return 15.0

    def _score_structure(self, sentences: list) -> float:
        """
        Score sentence structure quality.

        Args:
            sentences: List of spaCy sentence spans.

        Returns:
            Structure score 0-25.
        """
        if not sentences:
            return 0.0

        sentence_count = len(sentences)

        if sentence_count == 1:
            # Single sentence is often too short
            return 8.0
        elif sentence_count <= 5:
            return 25.0
        elif sentence_count <= 10:
            return 20.0
        else:
            return 15.0

    def _score_indicators(self, text: str) -> float:
        """
        Score use of structure indicator words.

        Args:
            text: Lowercase answer text.

        Returns:
            Indicator score 0-25.
        """
        found = [ind for ind in self.STRUCTURE_INDICATORS if ind in text]

        if len(found) == 0:
            return 10.0
        elif len(found) == 1:
            return 17.0
        elif len(found) == 2:
            return 22.0
        else:
            return 25.0

    def _score_grammar(self, doc) -> float:
        """
        Estimate grammar quality from spaCy parse.

        Args:
            doc: spaCy Doc object.

        Returns:
            Grammar score 0-25.
        """
        total_tokens = len([t for t in doc if not t.is_space])

        if total_tokens == 0:
            return 0.0

        # Check for root verbs in sentences (a sentence without a root verb
        # is often a fragment)
        sentences = list(doc.sents)
        if not sentences:
            return 0.0

        good_sentences = 0
        for sent in sentences:
            has_root = any(tok.dep_ == "ROOT" for tok in sent)
            has_subject = any(tok.dep_ in ("nsubj", "nsubjpass") for tok in sent)
            if has_root and has_subject:
                good_sentences += 1

        grammar_ratio = good_sentences / len(sentences) if sentences else 0.0
        return self._clamp(grammar_ratio * 25.0)

    def _detect_issues(self, doc, text: str) -> list[str]:
        """
        Detect specific grammar and style issues.

        Args:
            doc: spaCy Doc object.
            text: Raw answer text.

        Returns:
            List of detected issues.
        """
        issues = []

        sentences = list(doc.sents)
        for i, sent in enumerate(sentences):
            has_subject = any(
                tok.dep_ in ("nsubj", "nsubjpass") for tok in sent
            )
            if not has_subject and len(list(sent)) > 3:
                issues.append(f"Sentence {i + 1} may be a fragment (missing subject)")

        filler_found = [
            phrase for phrase in self.FILLER_PHRASES
            if phrase in text.lower()
        ]
        if filler_found:
            issues.append(f"Filler phrases detected: {', '.join(filler_found)}")

        return issues

    def _build_explanation(
        self,
        score: float,
        word_count: int,
        sentence_count: int,
        grammar_issues: list[str],
    ) -> tuple[str, list[str]]:
        """
        Build communication quality explanation.

        Args:
            score: Final communication score.
            word_count: Answer word count.
            sentence_count: Answer sentence count.
            grammar_issues: Detected issues.

        Returns:
            Tuple of (reason text, evidence list).
        """
        evidence = [
            f"Answer length: {word_count} words",
            f"Sentence count: {sentence_count}",
        ]
        if grammar_issues:
            evidence.extend(grammar_issues)

        if score >= 85:
            reason = (
                "Excellent communication. Your answer is well-structured, "
                "clear, and appropriately detailed. You use technical "
                "terminology correctly and guide the reader logically."
            )
        elif score >= 70:
            reason = (
                "Good communication overall. Your answer is clear and "
                "understandable. Minor improvements in structure or "
                "sentence variety could strengthen it further."
            )
        elif score >= 50:
            reason = (
                "Adequate communication but with noticeable issues. "
                "Consider organizing your answer more clearly, using "
                "structured connectors like 'firstly', 'additionally', "
                "and 'in conclusion' to guide the reader."
            )
        elif score >= 30:
            reason = (
                "Communication quality is below average. The answer may "
                "be too brief, lack clear structure, or contain grammatical "
                "issues that affect readability."
            )
        else:
            reason = (
                "Communication is significantly lacking. The answer is "
                "very brief, poorly structured, or difficult to follow. "
                "Practice explaining technical concepts clearly and concisely."
            )

        return reason, evidence
