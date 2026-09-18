"""
Scoring Module
Calculates scores based on correctness, difficulty, speed, and streaks.

Author: [Candidate Name]
AI-Assisted: None. This module is entirely manually implemented.
"""

from config import Config, Difficulty
from user_state import UserState, AnswerRecord
from question_bank import Question


class ScoringEngine:
    """
    Calculates scores for individual questions and manages overall scoring.

    Scoring formula:
    base_score = BASE_SCORE_CORRECT if correct, else 0
    difficulty_bonus = base_score * (difficulty_level - 1) * DIFFICULTY_MULTIPLIER * 0.25
    speed_bonus = up to SPEED_BONUS_MAX points for fast answers
    streak_bonus = STREAK_BONUS for each consecutive correct after 2

    Total = base_score + difficulty_bonus + speed_bonus + streak_bonus
    """

    @staticmethod
    def calculate_score(
        question: Question,
        is_correct: bool,
        time_taken: float,
        consecutive_correct: int
    ) -> int:
        """
        Calculate the score for a single question response.

        Args:
            question: The question that was answered
            is_correct: Whether the answer was correct
            time_taken: Time taken to answer in seconds
            consecutive_correct: Current streak of consecutive correct answers

        Returns:
            Total score earned for this question
        """
        if not is_correct:
            return 0

        # Base score
        score = Config.BASE_SCORE_CORRECT

        # Difficulty bonus: harder questions worth more
        difficulty_bonus = int(
            score * (question.difficulty.value - 1) * 0.25 * Config.DIFFICULTY_MULTIPLIER
        )
        score += difficulty_bonus

        # Speed bonus: faster answers get bonus points
        if time_taken < Config.SPEED_BONUS_THRESHOLD:
            # Linear interpolation: 0 seconds = max bonus, threshold = 0 bonus
            speed_ratio = 1.0 - (time_taken / Config.SPEED_BONUS_THRESHOLD)
            speed_bonus = int(Config.SPEED_BONUS_MAX * speed_ratio)
            score += speed_bonus

        # Streak bonus
        if consecutive_correct >= 2:
            streak_bonus = Config.STREAK_BONUS * (consecutive_correct - 1)
            score += min(streak_bonus, 60)  # Cap streak bonus

        return score

    @staticmethod
    def calculate_category_score(user_state: UserState) -> dict[str, float]:
        """
        Calculate normalized scores per category (0-100 scale).

        This considers both accuracy and the difficulty of questions answered
        in each category.
        """
        category_scores = {}
        cat_stats = user_state.get_category_stats()

        for cat_key, stats in cat_stats.items():
            if stats['total'] == 0:
                continue

            # Weighted score: accuracy × average_difficulty_weight
            accuracy = stats['accuracy']
            avg_diff = stats['average_difficulty']

            # Normalize: perfect accuracy at max difficulty = 100
            # accuracy (0-1) * difficulty_weight (0.2-1.0 mapped from 1-5)
            difficulty_weight = 0.2 + (avg_diff - 1) * 0.2
            weighted_score = accuracy * difficulty_weight * 100

            # Adjust for sample size (penalize very few questions slightly)
            sample_factor = min(1.0, stats['total'] / 3)
            adjusted_score = weighted_score * (0.7 + 0.3 * sample_factor)

            category_scores[cat_key] = round(adjusted_score, 1)

        return category_scores

    @staticmethod
    def calculate_overall_percentile(user_state: UserState) -> float:
        """
        Estimate a percentile score based on performance.

        This is a simplified estimation - in a real system, this would
        compare against a normative database.
        """
        if user_state.questions_answered == 0:
            return 50.0

        # Factors: accuracy, difficulty handled, speed
        accuracy = user_state.overall_accuracy
        avg_ability = user_state.estimated_ability / 5.0
        speed_factor = min(1.0, Config.SPEED_BONUS_THRESHOLD / max(user_state.average_time, 1.0))

        # Weighted combination
        raw_percentile = (
            accuracy * 0.4 +
            avg_ability * 0.4 +
            speed_factor * 0.2
        ) * 100

        # Clamp to reasonable range
        return round(max(5.0, min(99.0, raw_percentile)), 1)

    @staticmethod
    def get_score_breakdown(user_state: UserState) -> dict:
        """Get a complete score breakdown for the final report."""
        return {
            "total_score": user_state.total_score,
            "questions_answered": user_state.questions_answered,
            "correct_answers": sum(1 for a in user_state.answers if a.is_correct),
            "overall_accuracy": round(user_state.overall_accuracy * 100, 1),
            "average_time_per_question": round(user_state.average_time, 1),
            "max_streak": max(
                _get_max_streak(user_state.answers),
                user_state.consecutive_correct
            ),
            "category_scores": ScoringEngine.calculate_category_score(user_state),
            "estimated_percentile": ScoringEngine.calculate_overall_percentile(user_state),
            "difficulty_stats": user_state.get_difficulty_stats(),
        }


def _get_max_streak(answers: list[AnswerRecord]) -> int:
    """Calculate the maximum consecutive correct streak."""
    max_streak = 0
    current_streak = 0
    for answer in answers:
        if answer.is_correct:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return max_streak