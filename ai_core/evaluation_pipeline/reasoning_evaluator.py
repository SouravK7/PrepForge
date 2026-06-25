"""
Reasoning evaluator.

Measures the depth, logical structure, and argument
coherence of the user's answer.
"""

from __future__ import annotations

from ai_core.evaluation_pipeline.base_evaluator import BaseEvaluator, DimensionScore
from ai_core.shared.model_manager import model_manager
from ai_core.shared.text_processor import TextProcessor
from schemas.answer_schema import AnswerInput


class ReasoningEvaluator(BaseEvaluator):
    """
    Evaluates logical depth and reasoning quality.

    Measures argument structure, causal reasoning,
    comparative analysis, and explanation depth.
    """

    # Signals of causal and logical reasoning
    CAUSAL_SIGNALS = [
        "because", "therefore", "thus", "hence", "as a result",
        "consequently", "due to", "which means", "this leads to",
        "the reason is", "this causes", "this allows", "this ensures",
        "this prevents", "this enables",
    ]

    # Signals of comparative reasoning
    COMPARATIVE_SIGNALS = [
        "compared to", "whereas", "on the other hand", "however",
        "unlike", "in contrast", "while", "alternatively",
        "the difference between", "versus", "vs", "better than",
        "more efficient", "less efficient",
    ]

    # Signals of deep explanation
    DEPTH_SIGNALS = [
        "under the hood", "internally", "at a lower level",
        "the underlying", "the key insight", "the reason why",
        "fundamentally", "essentially", "in more detail",
        "to elaborate", "to be more specific", "specifically",
        "more precisely",
    ]

    @property
    def dimension_name(self) -> str:
        """Dimension name for this evaluator."""
        return "reasoning"

    def evaluate(self, answer_input: AnswerInput) -> DimensionScore:
        """
        Evaluate reasoning depth and logical structure.

        Args:
            answer_input: Contains user_answer.

        Returns:
            DimensionScore with reasoning quality score.
        """
        user_answer = answer_input.user_answer
        answer_lower = user_answer.lower()
        word_count = TextProcessor.word_count(user_answer)

        # --- Detect reasoning signals ---
        causal_found = [sig for sig in self.CAUSAL_SIGNALS if sig in answer_lower]
        comparative_found = [sig for sig in self.COMPARATIVE_SIGNALS if sig in answer_lower]
        depth_found = [sig for sig in self.DEPTH_SIGNALS if sig in answer_lower]

        # --- Score sentence-level complexity ---
        complexity_score = self._score_complexity(user_answer, word_count)

        # --- Calculate overall reasoning score ---
        score = self._calculate_score(
            causal=causal_found,
            comparative=comparative_found,
            depth=depth_found,
            complexity_score=complexity_score,
            word_count=word_count,
        )

        evidence = self._collect_evidence(causal_found, comparative_found, depth_found)

        reason, evidence_list = self._build_explanation(
            score=score,
            causal=causal_found,
            comparative=comparative_found,
            depth=depth_found,
            evidence=evidence,
        )

        return DimensionScore(
            score=round(score, 2),
            label="Reasoning and Depth",
            reason=reason,
            evidence=evidence_list,
        )

    def _score_complexity(self, text: str, word_count: int) -> float:
        """
        Score syntactic complexity of answer.

        Args:
            text: Answer text.
            word_count: Total word count.

        Returns:
            Complexity score 0-25.
        """
        nlp = model_manager.get_spacy_model()
        doc = nlp(text)

        sentences = list(doc.sents)
        if not sentences:
            return 0.0

        # Average sentence length
        avg_length = word_count / len(sentences) if sentences else 0

        # Prefer sentences of 10-25 words (complex but not rambling)
        if 10 <= avg_length <= 25:
            length_score = 25.0
        elif 7 <= avg_length < 10 or 25 < avg_length <= 35:
            length_score = 18.0
        else:
            length_score = 10.0

        return length_score

    def _calculate_score(
        self,
        causal: list[str],
        comparative: list[str],
        depth: list[str],
        complexity_score: float,
        word_count: int,
    ) -> float:
        """
        Calculate reasoning score from detected signals.

        Args:
            causal: Causal reasoning signals found.
            comparative: Comparative reasoning signals found.
            depth: Depth signals found.
            complexity_score: Syntactic complexity score.
            word_count: Total answer word count.

        Returns:
            Reasoning score 0-100.
        """
        score = 0.0

        # Causal reasoning worth up to 30 points
        if len(causal) >= 3:
            score += 30.0
        elif len(causal) == 2:
            score += 22.0
        elif len(causal) == 1:
            score += 13.0

        # Comparative reasoning worth up to 25 points
        if len(comparative) >= 2:
            score += 25.0
        elif len(comparative) == 1:
            score += 15.0

        # Depth signals worth up to 20 points
        if len(depth) >= 2:
            score += 20.0
        elif len(depth) == 1:
            score += 12.0

        # Syntactic complexity worth up to 25 points
        score += complexity_score

        # Bonus for sufficiently detailed answers
        if word_count >= 80 and (causal or comparative or depth):
            score = min(score + 5.0, 100.0)

        return self._clamp(score)

    def _collect_evidence(
        self,
        causal: list[str],
        comparative: list[str],
        depth: list[str],
    ) -> list[str]:
        """
        Collect evidence from found signals.

        Args:
            causal: Detected causal signals.
            comparative: Detected comparative signals.
            depth: Detected depth signals.

        Returns:
            List of evidence strings.
        """
        evidence = []

        if causal:
            evidence.append(
                f"Causal reasoning detected: {', '.join(causal[:3])}"
            )
        if comparative:
            evidence.append(
                f"Comparative reasoning detected: {', '.join(comparative[:3])}"
            )
        if depth:
            evidence.append(
                f"Depth signals detected: {', '.join(depth[:3])}"
            )
        if not evidence:
            evidence.append("No logical reasoning signals detected")

        return evidence

    def _build_explanation(
        self,
        score: float,
        causal: list[str],
        comparative: list[str],
        depth: list[str],
        evidence: list[str],
    ) -> tuple[str, list[str]]:
        """
        Build reasoning depth explanation.

        Args:
            score: Final reasoning score.
            causal: Detected causal reasoning phrases.
            comparative: Detected comparative reasoning phrases.
            depth: Detected depth signals.
            evidence: Collected evidence list.

        Returns:
            Tuple of (reason text, evidence list).
        """
        if score >= 80:
            reason = (
                "Excellent reasoning depth. Your answer demonstrates "
                "causal thinking, comparative analysis, or deep "
                "explanation that goes beyond surface-level recall. "
                "This is the hallmark of a strong candidate."
            )
        elif score >= 60:
            reason = (
                "Good reasoning. You show some logical structure and "
                "causal thinking. Adding more 'why' and 'how' explanations "
                "would push this to an excellent level."
            )
        elif score >= 40:
            reason = (
                "Moderate reasoning depth. Your answer tends to state "
                "facts without explaining the reasoning behind them. "
                "Try explaining why something works the way it does, "
                "not just what it does."
            )
        elif score >= 20:
            reason = (
                "Limited reasoning depth. The answer lacks explanatory "
                "depth. Use words like 'because', 'therefore', 'this means' "
                "to connect ideas and show logical thinking."
            )
        else:
            reason = (
                "No significant reasoning depth detected. The answer "
                "appears to be a list of facts or keywords without "
                "logical connection. Work on explaining not just what "
                "something is but how and why it works."
            )

        return reason, evidence
