"""
Structured AI decision logging.

Every AI decision is logged for transparency, debugging, and audit trails.
Logs are stored in logs/ai_decisions.log.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class AILogger:
    """
    Structured logger for all AI decisions.

    Every evaluation, recommendation, adaptation, and question
    selection decision is logged with full context for auditability.
    """

    def __init__(self, log_file: str = "logs/ai_decisions.log") -> None:
        """
        Initialize the AI logger.

        Args:
            log_file: Path to log file relative to project root.
        """
        self.log_file = Path(__file__).parent.parent.parent / log_file
        self.log_file.parent.mkdir(exist_ok=True)

        # Configure Python logging
        self.logger = logging.getLogger("ai_decisions")
        self.logger.setLevel(logging.INFO)

        # File handler
        handler = logging.FileHandler(self.log_file)
        handler.setLevel(logging.INFO)

        # Formatter: timestamp, level, message
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        # Avoid duplicate handlers
        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def log_decision(
        self,
        decision_type: str,
        context: dict[str, Any],
        output: dict[str, Any],
        reasoning: str,
        confidence: float = 1.0,
    ) -> None:
        """
        Log a significant AI decision.

        Args:
            decision_type: Type of decision
                          e.g. "question_selected", "answer_evaluated"
            context: Input context for this decision
            output: Decision output/result
            reasoning: Human-readable explanation of why
            confidence: Confidence in the decision 0.0-1.0
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "decision_type": decision_type,
            "context": context,
            "output": output,
            "reasoning": reasoning,
            "confidence": confidence,
        }

        self.logger.info(json.dumps(log_entry, default=str))

    def log_evaluation(
        self,
        session_id: int,
        question_id: str,
        scores: dict[str, float],
        final_score: float,
        grade: str,
    ) -> None:
        """
        Log an answer evaluation decision.

        Args:
            session_id: Interview session id
            question_id: Question being evaluated
            scores: Per-dimension scores
            final_score: Weighted final score
            grade: Letter grade
        """
        self.log_decision(
            decision_type="answer_evaluated",
            context={
                "session_id": session_id,
                "question_id": question_id,
            },
            output={
                "scores": scores,
                "final_score": final_score,
                "grade": grade,
            },
            reasoning="Answer processed through evaluation ensemble",
            confidence=1.0,
        )

    def log_competency_update(
        self,
        user_id: int,
        competency_id: str,
        old_confidence: float,
        new_confidence: float,
        delta: float,
    ) -> None:
        """
        Log a competency confidence update.

        Args:
            user_id: User being updated
            competency_id: Competency being updated
            old_confidence: Previous confidence
            new_confidence: Updated confidence
            delta: Change magnitude
        """
        self.log_decision(
            decision_type="competency_updated",
            context={
                "user_id": user_id,
                "competency_id": competency_id,
            },
            output={
                "old_confidence": old_confidence,
                "new_confidence": new_confidence,
                "delta": delta,
            },
            reasoning="Competency confidence updated after evaluation",
            confidence=1.0,
        )

    def log_question_selection(
        self,
        session_id: int,
        question_id: str,
        competency_id: str,
        reasoning: str,
        elo_difficulty: float,
        user_elo: float,
    ) -> None:
        """
        Log a question selection decision.

        Args:
            session_id: Interview session id
            question_id: Selected question id
            competency_id: Competency being tested
            reasoning: Why this question was selected
            elo_difficulty: Question Elo difficulty
            user_elo: User Elo rating for competency
        """
        self.log_decision(
            decision_type="question_selected",
            context={
                "session_id": session_id,
                "competency_id": competency_id,
                "user_elo": user_elo,
            },
            output={
                "question_id": question_id,
                "elo_difficulty": elo_difficulty,
            },
            reasoning=reasoning,
            confidence=1.0,
        )

    def log_recommendation_generated(
        self,
        user_id: int,
        competency_id: str,
        resource_id: Optional[str],
        reasoning: str,
    ) -> None:
        """
        Log a recommendation generation.

        Args:
            user_id: User receiving recommendation
            competency_id: Competency being addressed
            resource_id: Resource being recommended
            reasoning: Why this was recommended
        """
        self.log_decision(
            decision_type="recommendation_generated",
            context={
                "user_id": user_id,
                "competency_id": competency_id,
            },
            output={
                "resource_id": resource_id,
            },
            reasoning=reasoning,
            confidence=1.0,
        )


# Global logger instance
ai_logger = AILogger()
