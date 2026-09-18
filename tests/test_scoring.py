"""
Tests for the Scoring Engine.

Author: [Candidate Name]
"""

import pytest
from scoring import ScoringEngine
from question_bank import Question
from config import Difficulty, CognitiveCategory


@pytest.fixture
def easy_question():
    return Question(
        id="TEST-01",
        text="Test question",
        options=["A", "B", "C", "D"],
        correct_answer=0,
        difficulty=Difficulty.EASY,
        category=CognitiveCategory.LOGICAL_REASONING,
        explanation="Test explanation",
    )


@pytest.fixture
def hard_question():
    return Question(
        id="TEST-02",
        text="Hard test question",
        options=["A", "B", "C", "D"],
        correct_answer=0,
        difficulty=Difficulty.VERY_HARD,
        category=CognitiveCategory.LOGICAL_REASONING,
        explanation="Test explanation",
    )


def test_correct_answer_scores_positive(easy_question):
    score = ScoringEngine.calculate_score(easy_question, True, 15.0, 0)
    assert score > 0


def test_wrong_answer_scores_zero(easy_question):
    score = ScoringEngine.calculate_score(easy_question, False, 15.0, 0)
    assert score == 0


def test_harder_questions_score_more(easy_question, hard_question):
    easy_score = ScoringEngine.calculate_score(easy_question, True, 15.0, 0)
    hard_score = ScoringEngine.calculate_score(hard_question, True, 15.0, 0)
    assert hard_score > easy_score


def test_speed_bonus(easy_question):
    slow_score = ScoringEngine.calculate_score(easy_question, True, 30.0, 0)
    fast_score = ScoringEngine.calculate_score(easy_question, True, 3.0, 0)
    assert fast_score > slow_score


def test_streak_bonus(easy_question):
    no_streak_score = ScoringEngine.calculate_score(easy_question, True, 15.0, 0)
    streak_score = ScoringEngine.calculate_score(easy_question, True, 15.0, 5)
    assert streak_score > no_streak_score