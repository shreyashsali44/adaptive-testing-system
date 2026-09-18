"""
Test Runner Module
Orchestrates the complete test flow, connecting all components.

Author: [Candidate Name]
AI-Assisted: None. Entirely manual implementation of the orchestration logic.
"""

import time
import logging
from typing import Optional, Callable
from config import Config, Difficulty
from question_bank import QuestionBank, Question
from user_state import UserState, AnswerRecord
from adaptive_engine import AdaptiveEngine
from scoring import ScoringEngine
from cognitive_profile import CognitiveProfileGenerator
from explanation_engine import ExplanationEngine
from llm_integration import get_llm

logger = logging.getLogger(__name__)


class TestSession:
    """
    Manages a complete adaptive test session.

    This is the main orchestrator that coordinates:
    - Question selection via AdaptiveEngine
    - Answer recording via UserState
    - Score calculation via ScoringEngine
    - Profile generation via CognitiveProfileGenerator
    """

    def __init__(self, user_id: str = "default", max_questions: Optional[int] = None):
        self.question_bank = QuestionBank()
        self.user_state = UserState(user_id=user_id)
        self.adaptive_engine = AdaptiveEngine(self.question_bank)
        self.scoring_engine = ScoringEngine()
        self.explanation_engine = ExplanationEngine()
        self.llm = get_llm()
        self.max_questions = max_questions or Config.MAX_QUESTIONS
        self.is_active = True
        self.current_question: Optional[Question] = None
        self.current_explanation: str = ""
        self._question_start_time: Optional[float] = None

        logger.info(f"Test session created for user {user_id} with max {self.max_questions} questions.")

    def get_next_question(self) -> Optional[dict]:
        """
        Get the next question for the test.

        Returns:
            Dictionary with question data, or None if the test is over.
        """
        if not self.is_active:
            return None

        if self.user_state.questions_answered >= self.max_questions:
            self.is_active = False
            return None

        # Check if we have questions left
        remaining = len(self.question_bank.questions) - len(self.user_state.asked_question_ids)
        if remaining == 0:
            self.is_active = False
            return None

        try:
            question, explanation = self.adaptive_engine.select_next_question(self.user_state)
            self.current_question = question
            self.current_explanation = explanation
            self._question_start_time = time.time()
            self.user_state.start_question_timer()

            # Get strategy explanation
            strategy = self.explanation_engine.explain_overall_strategy(self.user_state)

            return {
                "question_number": self.user_state.questions_answered + 1,
                "total_questions": self.max_questions,
                "question_id": question.id,
                "text": question.text,
                "options": question.options,
                "difficulty": str(question.difficulty),
                "category": str(question.category),
                "time_limit": question.time_limit,
                "adaptive_explanation": explanation,
                "strategy": strategy,
                "current_score": self.user_state.total_score,
                "estimated_ability": round(self.user_state.estimated_ability, 2),
            }

        except RuntimeError as e:
            logger.error(f"Error selecting question: {e}")
            self.is_active = False
            return None

    def submit_answer(self, selected_answer: int, confidence: Optional[str] = None) -> dict:
        """
        Submit an answer for the current question.

        Args:
            selected_answer: Index of the selected answer (0-based)
            confidence: User's self-reported confidence level

        Returns:
            Dictionary with result details
        """
        if self.current_question is None:
            return {"error": "No active question. Call get_next_question first."}

        question = self.current_question
        time_taken = time.time() - self._question_start_time if self._question_start_time else 0

        # Determine correctness
        is_correct = selected_answer == question.correct_answer

        # Calculate score
        score = self.scoring_engine.calculate_score(
            question=question,
            is_correct=is_correct,
            time_taken=time_taken,
            consecutive_correct=self.user_state.consecutive_correct
        )

        # Create answer record
        record = AnswerRecord(
            question_id=question.id,
            question_difficulty=question.difficulty,
            question_category=question.category,
            selected_answer=selected_answer,
            correct_answer=question.correct_answer,
            is_correct=is_correct,
            time_taken=time_taken,
            score_earned=score,
            confidence=confidence,
        )

        # Record the answer (updates all state)
        self.user_state.record_answer(record)

        # Generate feedback
        feedback = self.llm.generate_answer_feedback(
            question_text=question.text,
            correct_answer=question.options[question.correct_answer],
            user_answer=question.options[selected_answer] if 0 <= selected_answer < len(question.options) else "Invalid",
            is_correct=is_correct,
            explanation=question.explanation,
        )

        # Generate difficulty change explanation
        diff_explanation = ""
        if self.user_state.questions_answered >= 2:
            prev_diff = self.user_state.answers[-2].question_difficulty if len(self.user_state.answers) >= 2 else Difficulty.MEDIUM
            curr_diff = self.user_state.current_difficulty
            diff_explanation = self.explanation_engine.explain_difficulty_change(
                prev_diff, curr_diff, self.user_state
            )

        # Check if test is over
        is_last = self.user_state.questions_answered >= self.max_questions
        if is_last:
            self.is_active = False

        result = {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "correct_answer_text": question.options[question.correct_answer],
            "score_earned": score,
            "total_score": self.user_state.total_score,
            "time_taken": round(time_taken, 1),
            "feedback": feedback,
            "explanation": question.explanation,
            "difficulty_explanation": diff_explanation,
            "adaptive_explanation": self.current_explanation,
            "current_stats": {
                "accuracy": round(self.user_state.overall_accuracy * 100, 1),
                "estimated_ability": round(self.user_state.estimated_ability, 2),
                "consecutive_correct": self.user_state.consecutive_correct,
                "consecutive_wrong": self.user_state.consecutive_wrong,
            },
            "is_test_complete": is_last,
        }

        self.current_question = None
        return result

    def get_final_results(self) -> dict:
        """
        Generate the final test results and cognitive profile.

        Returns:
            Comprehensive results dictionary
        """
        profile_gen = CognitiveProfileGenerator(self.user_state)
        profile = profile_gen.generate_full_profile()

        # Add decision log
        decision_log = self.explanation_engine.format_decision_log(self.user_state)

        return {
            "profile": profile,
            "decision_log": decision_log,
            "session_data": self.user_state.to_dict(),
        }

    def get_progress(self) -> dict:
        """Get current test progress."""
        return {
            "questions_answered": self.user_state.questions_answered,
            "total_questions": self.max_questions,
            "progress_percentage": round(
                self.user_state.questions_answered / self.max_questions * 100, 1
            ),
            "total_score": self.user_state.total_score,
            "accuracy": round(self.user_state.overall_accuracy * 100, 1),
            "is_active": self.is_active,
        }