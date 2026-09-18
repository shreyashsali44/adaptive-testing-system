"""
User State Management Module
Tracks all aspects of user performance and test state throughout the session.

Author: [Candidate Name]
AI-Assisted: Data class structure reviewed with AI. Core state management
logic and performance tracking algorithms are manual implementations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from config import Difficulty, CognitiveCategory, Config
import json
import time


@dataclass
class AnswerRecord:
    """Records details of a single answer."""
    question_id: str
    question_difficulty: Difficulty
    question_category: CognitiveCategory
    selected_answer: int
    correct_answer: int
    is_correct: bool
    time_taken: float  # seconds
    score_earned: int
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: Optional[str] = None  # User's self-reported confidence

    def to_dict(self) -> dict:
        return {
            "question_id": self.question_id,
            "difficulty": self.question_difficulty.value,
            "category": self.question_category.value,
            "selected_answer": self.selected_answer,
            "correct_answer": self.correct_answer,
            "is_correct": self.is_correct,
            "time_taken": round(self.time_taken, 2),
            "score_earned": self.score_earned,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
        }


@dataclass
class AdaptiveDecision:
    """Records why a particular question was selected."""
    question_id: str
    target_difficulty: Difficulty
    target_category: Optional[CognitiveCategory]
    reasoning: str
    factors: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "question_id": self.question_id,
            "target_difficulty": self.target_difficulty.value,
            "target_category": self.target_category.value if self.target_category else None,
            "reasoning": self.reasoning,
            "factors": self.factors,
            "timestamp": self.timestamp.isoformat(),
        }


class UserState:
    """
    Maintains the complete state of a user's test session.

    This is the central state management component that tracks:
    - Answer history
    - Performance metrics by category and difficulty
    - Consecutive streaks
    - Current estimated ability level
    - Adaptive decision history
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.session_start = datetime.now()
        self.answers: list[AnswerRecord] = []
        self.adaptive_decisions: list[AdaptiveDecision] = []
        self.asked_question_ids: set[str] = set()
        self.total_score: int = 0
        self.current_difficulty: Difficulty = Config.INITIAL_DIFFICULTY
        self.estimated_ability: float = 3.0  # Scale 1-5, starts at medium
        self.consecutive_correct: int = 0
        self.consecutive_wrong: int = 0

        # Per-category tracking
        self._category_correct: dict[str, int] = {}
        self._category_total: dict[str, int] = {}
        self._category_difficulty_sum: dict[str, float] = {}

        # Per-difficulty tracking
        self._difficulty_correct: dict[int, int] = {}
        self._difficulty_total: dict[int, int] = {}

        # Timing tracking
        self._total_time: float = 0.0
        self._question_start_time: Optional[float] = None

    def start_question_timer(self):
        """Start timing the current question."""
        self._question_start_time = time.time()

    def get_elapsed_time(self) -> float:
        """Get time elapsed since question timer started."""
        if self._question_start_time is None:
            return 0.0
        return time.time() - self._question_start_time

    def record_answer(self, record: AnswerRecord):
        """
        Record an answer and update all internal state.

        This is the primary state mutation method. It updates:
        - Answer history
        - Category and difficulty statistics
        - Consecutive streaks
        - Estimated ability level
        - Total score
        """
        self.answers.append(record)
        self.asked_question_ids.add(record.question_id)
        self.total_score += record.score_earned
        self._total_time += record.time_taken

        # Update category tracking
        cat_key = record.question_category.value
        self._category_correct[cat_key] = self._category_correct.get(cat_key, 0) + (1 if record.is_correct else 0)
        self._category_total[cat_key] = self._category_total.get(cat_key, 0) + 1
        self._category_difficulty_sum[cat_key] = self._category_difficulty_sum.get(cat_key, 0.0) + record.question_difficulty.value

        # Update difficulty tracking
        diff_key = record.question_difficulty.value
        self._difficulty_correct[diff_key] = self._difficulty_correct.get(diff_key, 0) + (1 if record.is_correct else 0)
        self._difficulty_total[diff_key] = self._difficulty_total.get(diff_key, 0) + 1

        # Update streaks
        if record.is_correct:
            self.consecutive_correct += 1
            self.consecutive_wrong = 0
        else:
            self.consecutive_wrong += 1
            self.consecutive_correct = 0

        # Update estimated ability using exponential moving average
        self._update_estimated_ability(record)

    def _update_estimated_ability(self, record: AnswerRecord):
        """
        Update the estimated ability level using a weighted approach.

        The ability estimate considers:
        1. Whether the answer was correct
        2. The difficulty of the question answered
        3. Recent performance trend (recency bias)

        This is the core adaptive signal that drives question selection.
        """
        # Performance signal: correct at high difficulty = high ability signal
        if record.is_correct:
            performance_signal = record.question_difficulty.value + 0.5
        else:
            performance_signal = record.question_difficulty.value - 1.0

        # Clamp the signal
        performance_signal = max(1.0, min(5.0, performance_signal))

        # Exponential moving average with recency weight
        alpha = 0.3  # How much to weight the new signal
        self.estimated_ability = (1 - alpha) * self.estimated_ability + alpha * performance_signal

        # Apply streak bonuses/penalties
        if self.consecutive_correct >= Config.CONSECUTIVE_CORRECT_BOOST:
            self.estimated_ability = min(5.0, self.estimated_ability + 0.2)
        elif self.consecutive_wrong >= Config.CONSECUTIVE_WRONG_DROP:
            self.estimated_ability = max(1.0, self.estimated_ability - 0.2)

        # Ensure bounds
        self.estimated_ability = max(1.0, min(5.0, self.estimated_ability))

    def record_adaptive_decision(self, decision: AdaptiveDecision):
        """Record why a particular question was selected."""
        self.adaptive_decisions.append(decision)

    @property
    def questions_answered(self) -> int:
        return len(self.answers)

    @property
    def overall_accuracy(self) -> float:
        if not self.answers:
            return 0.0
        correct = sum(1 for a in self.answers if a.is_correct)
        return correct / len(self.answers)

    @property
    def recent_accuracy(self) -> float:
        """Accuracy over the last 3 questions (or all if fewer)."""
        recent = self.answers[-3:] if len(self.answers) >= 3 else self.answers
        if not recent:
            return 0.0
        correct = sum(1 for a in recent if a.is_correct)
        return correct / len(recent)

    @property
    def average_time(self) -> float:
        if not self.answers:
            return 0.0
        return self._total_time / len(self.answers)

    def get_category_accuracy(self, category: CognitiveCategory) -> Optional[float]:
        """Get accuracy for a specific cognitive category."""
        cat_key = category.value
        total = self._category_total.get(cat_key, 0)
        if total == 0:
            return None
        return self._category_correct.get(cat_key, 0) / total

    def get_category_stats(self) -> dict[str, dict]:
        """Get detailed stats for each attempted category."""
        stats = {}
        for cat_key, total in self._category_total.items():
            correct = self._category_correct.get(cat_key, 0)
            avg_diff = self._category_difficulty_sum.get(cat_key, 0) / total if total > 0 else 0
            stats[cat_key] = {
                "total": total,
                "correct": correct,
                "accuracy": round(correct / total, 3) if total > 0 else 0,
                "average_difficulty": round(avg_diff, 2),
            }
        return stats

    def get_difficulty_stats(self) -> dict[int, dict]:
        """Get performance stats by difficulty level."""
        stats = {}
        for diff_val, total in self._difficulty_total.items():
            correct = self._difficulty_correct.get(diff_val, 0)
            stats[diff_val] = {
                "total": total,
                "correct": correct,
                "accuracy": round(correct / total, 3) if total > 0 else 0,
            }
        return stats

    def get_least_tested_categories(self, all_categories: list[CognitiveCategory]) -> list[CognitiveCategory]:
        """Get categories with the least questions asked, for diversity."""
        category_counts = {cat.value: 0 for cat in all_categories}
        for answer in self.answers:
            category_counts[answer.question_category.value] = category_counts.get(answer.question_category.value, 0) + 1

        min_count = min(category_counts.values()) if category_counts else 0
        return [cat for cat in all_categories if category_counts.get(cat.value, 0) == min_count]

    def get_weakest_categories(self, min_questions: int = 1) -> list[CognitiveCategory]:
        """Get categories where user performs worst."""
        weak = []
        for cat_key, total in self._category_total.items():
            if total >= min_questions:
                accuracy = self._category_correct.get(cat_key, 0) / total
                if accuracy < Config.DIFFICULTY_DECREASE_THRESHOLD:
                    weak.append(CognitiveCategory(cat_key))
        return weak

    def get_strongest_categories(self, min_questions: int = 1) -> list[CognitiveCategory]:
        """Get categories where user performs best."""
        strong = []
        for cat_key, total in self._category_total.items():
            if total >= min_questions:
                accuracy = self._category_correct.get(cat_key, 0) / total
                if accuracy >= Config.DIFFICULTY_INCREASE_THRESHOLD:
                    strong.append(CognitiveCategory(cat_key))
        return strong

    def to_dict(self) -> dict:
        """Serialize complete state to dictionary."""
        return {
            "user_id": self.user_id,
            "session_start": self.session_start.isoformat(),
            "questions_answered": self.questions_answered,
            "total_score": self.total_score,
            "overall_accuracy": round(self.overall_accuracy, 3),
            "recent_accuracy": round(self.recent_accuracy, 3),
            "estimated_ability": round(self.estimated_ability, 2),
            "current_difficulty": self.current_difficulty.value,
            "consecutive_correct": self.consecutive_correct,
            "consecutive_wrong": self.consecutive_wrong,
            "average_time": round(self.average_time, 2),
            "category_stats": self.get_category_stats(),
            "difficulty_stats": self.get_difficulty_stats(),
            "answers": [a.to_dict() for a in self.answers],
            "adaptive_decisions": [d.to_dict() for d in self.adaptive_decisions],
        }

    def get_summary_for_llm(self) -> str:
        """Generate a concise summary string suitable for LLM context."""
        summary = f"""User Test State Summary:
- Questions answered: {self.questions_answered}
- Overall accuracy: {self.overall_accuracy:.1%}
- Recent accuracy (last 3): {self.recent_accuracy:.1%}
- Estimated ability: {self.estimated_ability:.2f}/5.0
- Current difficulty: {self.current_difficulty}
- Consecutive correct: {self.consecutive_correct}
- Consecutive wrong: {self.consecutive_wrong}
- Average response time: {self.average_time:.1f}s
- Total score: {self.total_score}
"""
        cat_stats = self.get_category_stats()
        if cat_stats:
            summary += "\nCategory Performance:\n"
            for cat_key, stats in cat_stats.items():
                cat_name = cat_key.replace('_', ' ').title()
                summary += f"  - {cat_name}: {stats['accuracy']:.0%} ({stats['correct']}/{stats['total']}) avg_diff={stats['average_difficulty']}\n"

        return summary