"""
Configuration module for the Adaptive Testing System.
Handles environment variables, constants, and system-wide settings.

Author: [Candidate Name]
AI-Assisted: Configuration structure reviewed with AI assistance.
Core logic and parameter tuning: Manual implementation.
"""

import os
from dotenv import load_dotenv
from enum import Enum
from typing import Optional

load_dotenv()


class Difficulty(Enum):
    VERY_EASY = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    VERY_HARD = 5

    @classmethod
    def from_value(cls, value: int) -> 'Difficulty':
        """Convert integer to Difficulty enum with bounds checking."""
        clamped = max(1, min(5, value))
        return cls(clamped)

    def __str__(self):
        return self.name.replace('_', ' ').title()


class CognitiveCategory(Enum):
    LOGICAL_REASONING = "logical_reasoning"
    PATTERN_RECOGNITION = "pattern_recognition"
    VERBAL_REASONING = "verbal_reasoning"
    NUMERICAL_REASONING = "numerical_reasoning"
    SPATIAL_REASONING = "spatial_reasoning"
    WORKING_MEMORY = "working_memory"
    CRITICAL_THINKING = "critical_thinking"

    def __str__(self):
        return self.value.replace('_', ' ').title()


class Config:
    """Central configuration for the adaptive testing system."""

    # API Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")

    # Test Parameters
    MAX_QUESTIONS: int = int(os.getenv("MAX_QUESTIONS", "10"))
    MIN_QUESTIONS: int = 5
    TOTAL_QUESTION_BANK_SIZE: int = 25

    # Adaptive Engine Parameters
    INITIAL_DIFFICULTY: Difficulty = Difficulty.MEDIUM
    DIFFICULTY_INCREASE_THRESHOLD: float = 0.7  # Score above this → harder
    DIFFICULTY_DECREASE_THRESHOLD: float = 0.4  # Score below this → easier
    CONSECUTIVE_CORRECT_BOOST: int = 2  # Consecutive correct to jump difficulty
    CONSECUTIVE_WRONG_DROP: int = 2  # Consecutive wrong to drop difficulty
    CATEGORY_ROTATION_WEIGHT: float = 0.3  # Weight for category diversity
    PERFORMANCE_WEIGHT: float = 0.5  # Weight for performance-based selection
    RECENCY_WEIGHT: float = 0.2  # Weight for recent performance vs overall

    # Scoring Parameters
    BASE_SCORE_CORRECT: int = 100
    DIFFICULTY_MULTIPLIER: float = 1.5
    SPEED_BONUS_THRESHOLD: float = 10.0  # seconds
    SPEED_BONUS_MAX: int = 20
    STREAK_BONUS: int = 15

    # Confidence Tracking
    CONFIDENCE_LEVELS = ["very_low", "low", "medium", "high", "very_high"]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration and return list of warnings."""
        warnings = []
        if not cls.OPENAI_API_KEY:
            warnings.append("OPENAI_API_KEY not set. LLM features will use fallback mode.")
        if cls.MAX_QUESTIONS > cls.TOTAL_QUESTION_BANK_SIZE:
            warnings.append(
                f"MAX_QUESTIONS ({cls.MAX_QUESTIONS}) exceeds bank size ({cls.TOTAL_QUESTION_BANK_SIZE}). "
                f"Adjusting to {cls.TOTAL_QUESTION_BANK_SIZE}."
            )
            cls.MAX_QUESTIONS = cls.TOTAL_QUESTION_BANK_SIZE
        return warnings