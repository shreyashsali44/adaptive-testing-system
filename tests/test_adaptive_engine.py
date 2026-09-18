"""
Tests for the Adaptive Engine.
Verifies that the question selection logic behaves correctly.

Author: [Candidate Name]
"""

import pytest
from adaptive_engine import AdaptiveEngine
from question_bank import QuestionBank
from user_state import UserState, AnswerRecord
from config import Difficulty, CognitiveCategory


@pytest.fixture
def engine():
    return AdaptiveEngine(QuestionBank())


@pytest.fixture
def user_state():
    return UserState(user_id="test_user")


def test_initial_question_is_medium(engine, user_state):
    """First question should be medium difficulty."""
    question, explanation = engine.select_next_question(user_state)
    assert question.difficulty == Difficulty.MEDIUM
    assert "First question" in explanation or "baseline" in explanation.lower()


def test_difficulty_increases_after_correct_answers(engine, user_state):
    """Difficulty should increase after consecutive correct answers."""
    # Simulate 3 correct answers at medium difficulty
    for i in range(3):
        q, _ = engine.select_next_question(user_state)
        record = AnswerRecord(
            question_id=q.id,
            question_difficulty=q.difficulty,
            question_category=q.category,
            selected_answer=q.correct_answer,
            correct_answer=q.correct_answer,
            is_correct=True,
            time_taken=10.0,
            score_earned=100,
        )
        user_state.record_answer(record)

    # Next question should be harder
    assert user_state.estimated_ability > 3.0
    assert user_state.consecutive_correct == 3


def test_difficulty_decreases_after_wrong_answers(engine, user_state):
    """Difficulty should decrease after consecutive wrong answers."""
    # Simulate 3 wrong answers
    for i in range(3):
        q, _ = engine.select_next_question(user_state)
        wrong_answer = (q.correct_answer + 1) % len(q.options)
        record = AnswerRecord(
            question_id=q.id,
            question_difficulty=q.difficulty,
            question_category=q.category,
            selected_answer=wrong_answer,
            correct_answer=q.correct_answer,
            is_correct=False,
            time_taken=15.0,
            score_earned=0,
        )
        user_state.record_answer(record)

    # Ability should decrease
    assert user_state.estimated_ability < 3.0
    assert user_state.consecutive_wrong == 3


def test_no_repeated_questions(engine, user_state):
    """Questions should not be repeated."""
    asked_ids = set()
    for i in range(8):
        q, _ = engine.select_next_question(user_state)
        assert q.id not in asked_ids, f"Question {q.id} was repeated!"
        asked_ids.add(q.id)

        record = AnswerRecord(
            question_id=q.id,
            question_difficulty=q.difficulty,
            question_category=q.category,
            selected_answer=q.correct_answer,
            correct_answer=q.correct_answer,
            is_correct=True,
            time_taken=10.0,
            score_earned=100,
        )
        user_state.record_answer(record)


def test_explanation_generated(engine, user_state):
    """Each question selection should come with an explanation."""
    q, explanation = engine.select_next_question(user_state)
    assert len(explanation) > 10
    assert isinstance(explanation, str)