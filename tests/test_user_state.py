"""
Tests for User State Management.

Author: [Candidate Name]
"""

import pytest
from user_state import UserState, AnswerRecord
from config import Difficulty, CognitiveCategory


@pytest.fixture
def state():
    return UserState(user_id="test")


def test_initial_state(state):
    assert state.questions_answered == 0
    assert state.overall_accuracy == 0.0
    assert state.estimated_ability == 3.0
    assert state.total_score == 0


def test_record_correct_answer(state):
    record = AnswerRecord(
        question_id="Q1",
        question_difficulty=Difficulty.MEDIUM,
        question_category=CognitiveCategory.LOGICAL_REASONING,
        selected_answer=0,
        correct_answer=0,
        is_correct=True,
        time_taken=10.0,
        score_earned=100,
    )
    state.record_answer(record)

    assert state.questions_answered == 1
    assert state.overall_accuracy == 1.0
    assert state.consecutive_correct == 1
    assert state.consecutive_wrong == 0
    assert state.total_score == 100


def test_record_wrong_answer(state):
    record = AnswerRecord(
        question_id="Q1",
        question_difficulty=Difficulty.MEDIUM,
        question_category=CognitiveCategory.LOGICAL_REASONING,
        selected_answer=1,
        correct_answer=0,
        is_correct=False,
        time_taken=10.0,
        score_earned=0,
    )
    state.record_answer(record)

    assert state.overall_accuracy == 0.0
    assert state.consecutive_wrong == 1


def test_ability_increases_with_correct(state):
    initial_ability = state.estimated_ability
    for i in range(3):
        record = AnswerRecord(
            question_id=f"Q{i}",
            question_difficulty=Difficulty.HARD,
            question_category=CognitiveCategory.LOGICAL_REASONING,
            selected_answer=0,
            correct_answer=0,
            is_correct=True,
            time_taken=10.0,
            score_earned=150,
        )
        state.record_answer(record)

    assert state.estimated_ability > initial_ability


def test_ability_decreases_with_wrong(state):
    initial_ability = state.estimated_ability
    for i in range(3):
        record = AnswerRecord(
            question_id=f"Q{i}",
            question_difficulty=Difficulty.EASY,
            question_category=CognitiveCategory.LOGICAL_REASONING,
            selected_answer=1,
            correct_answer=0,
            is_correct=False,
            time_taken=10.0,
            score_earned=0,
        )
        state.record_answer(record)

    assert state.estimated_ability < initial_ability


def test_category_tracking(state):
    record = AnswerRecord(
        question_id="Q1",
        question_difficulty=Difficulty.MEDIUM,
        question_category=CognitiveCategory.PATTERN_RECOGNITION,
        selected_answer=0,
        correct_answer=0,
        is_correct=True,
        time_taken=10.0,
        score_earned=100,
    )
    state.record_answer(record)

    acc = state.get_category_accuracy(CognitiveCategory.PATTERN_RECOGNITION)
    assert acc == 1.0

    # Untested category should return None
    acc2 = state.get_category_accuracy(CognitiveCategory.VERBAL_REASONING)
    assert acc2 is None


def test_serialization(state):
    record = AnswerRecord(
        question_id="Q1",
        question_difficulty=Difficulty.MEDIUM,
        question_category=CognitiveCategory.LOGICAL_REASONING,
        selected_answer=0,
        correct_answer=0,
        is_correct=True,
        time_taken=10.0,
        score_earned=100,
    )
    state.record_answer(record)

    data = state.to_dict()
    assert data['user_id'] == 'test'
    assert data['questions_answered'] == 1
    assert len(data['answers']) == 1