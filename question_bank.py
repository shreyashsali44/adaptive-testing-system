"""
Question Bank Module
Contains 25 questions across multiple cognitive categories and difficulty levels.

Author: [Candidate Name]
AI-Assisted: Some question content was generated with AI assistance and then
manually reviewed, curated, and categorized. The data structure, categorization
logic, and difficulty calibration are manual implementations.
"""

from dataclasses import dataclass, field
from typing import Optional
from config import Difficulty, CognitiveCategory
import json
import os


@dataclass
class Question:
    """Represents a single question in the adaptive test."""
    id: str
    text: str
    options: list[str]
    correct_answer: int  # Index of correct option (0-based)
    difficulty: Difficulty
    category: CognitiveCategory
    explanation: str
    time_limit: int = 60  # seconds
    tags: list[str] = field(default_factory=list)
    times_shown: int = 0
    times_correct: int = 0

    @property
    def historical_accuracy(self) -> Optional[float]:
        """Calculate historical accuracy rate for this question."""
        if self.times_shown == 0:
            return None
        return self.times_correct / self.times_shown

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "difficulty": self.difficulty.value,
            "category": self.category.value,
            "explanation": self.explanation,
            "time_limit": self.time_limit,
            "tags": self.tags,
        }


def get_question_bank() -> list[Question]:
    """
    Returns the complete question bank with 25 questions.
    Questions span 7 cognitive categories and 5 difficulty levels.
    """
    questions = [
        # ===== LOGICAL REASONING =====
        Question(
            id="LR-01",
            text="All roses are flowers. Some flowers fade quickly. Which conclusion is valid?",
            options=[
                "All roses fade quickly",
                "Some roses may fade quickly",
                "No roses fade quickly",
                "All flowers are roses"
            ],
            correct_answer=1,
            difficulty=Difficulty.EASY,
            category=CognitiveCategory.LOGICAL_REASONING,
            explanation="'Some flowers fade quickly' doesn't mean all do. Since roses are flowers, some roses MAY fade quickly, but it's not certain for all.",
            tags=["syllogism", "deduction"]
        ),
        Question(
            id="LR-02",
            text="If it rains, the ground gets wet. The ground is wet. What can we conclude?",
            options=[
                "It definitely rained",
                "It might have rained, but something else could have caused the wetness",
                "It did not rain",
                "The ground is always wet"
            ],
            correct_answer=1,
            difficulty=Difficulty.MEDIUM,
            category=CognitiveCategory.LOGICAL_REASONING,
            explanation="This is the fallacy of affirming the consequent. The ground being wet doesn't prove rain—a sprinkler could also cause it.",
            tags=["fallacy", "conditional"]
        ),
        Question(
            id="LR-03",
            text="In a group of 5 people (A, B, C, D, E): A is taller than B. C is shorter than D. B is taller than D. E is shorter than B but taller than D. Who is the shortest?",
            options=["B", "C", "D", "E"],
            correct_answer=1,
            difficulty=Difficulty.HARD,
            category=CognitiveCategory.LOGICAL_REASONING,
            explanation="From the clues: A > B > E > D > C. So C is the shortest. We know B > D and D > C, and E is between B and D.",
            tags=["ordering", "transitive"]
        ),
        Question(
            id="LR-04",
            text="Statement: 'No cats are dogs. All dogs are animals.' Which must be true?",
            options=[
                "No cats are animals",
                "All animals are dogs",
                "Some animals are not cats",
                "All cats are animals"
            ],
            correct_answer=2,
            difficulty=Difficulty.VERY_HARD,
            category=CognitiveCategory.LOGICAL_REASONING,
            explanation="Since all dogs are animals and no cats are dogs, the dogs that are animals are definitely not cats. So some animals (at least the dogs) are not cats.",
            tags=["syllogism", "sets"]
        ),

        # ===== PATTERN RECOGNITION =====
        Question(
            id="PR-01",
            text="What comes next in the sequence: 2, 6, 12, 20, 30, ?",
            options=["40", "42", "36", "38"],
            correct_answer=1,
            difficulty=Difficulty.EASY,
            category=CognitiveCategory.PATTERN_RECOGNITION,
            explanation="Differences: 4, 6, 8, 10, 12. Each difference increases by 2. So 30 + 12 = 42.",
            tags=["number_sequence", "arithmetic"]
        ),
        Question(
            id="PR-02",
            text="Find the pattern: 1, 1, 2, 3, 5, 8, 13, ?",
            options=["18", "20", "21", "15"],
            correct_answer=2,
            difficulty=Difficulty.VERY_EASY,
            category=CognitiveCategory.PATTERN_RECOGNITION,
            explanation="Fibonacci sequence: each number is the sum of the two preceding ones. 8 + 13 = 21.",
            tags=["fibonacci", "number_sequence"]
        ),
        Question(
            id="PR-03",
            text="What comes next: A1, C3, F6, J10, ?",
            options=["O15", "N14", "M13", "P16"],
            correct_answer=0,
            difficulty=Difficulty.HARD,
            category=CognitiveCategory.PATTERN_RECOGNITION,
            explanation="Letters jump by 2, 3, 4, 5 positions (A→C→F→J→O). Numbers are triangular: 1, 3, 6, 10, 15.",
            tags=["mixed_pattern", "alphanumeric"]
        ),
        Question(
            id="PR-04",
            text="In the sequence 3, 9, 27, 81, each number is obtained by:",
            options=[
                "Adding 6",
                "Multiplying by 3",
                "Squaring",
                "Adding the previous two numbers"
            ],
            correct_answer=1,
            difficulty=Difficulty.VERY_EASY,
            category=CognitiveCategory.PATTERN_RECOGNITION,
            explanation="Each number is 3 times the previous: 3×3=9, 9×3=27, 27×3=81. Geometric progression with ratio 3.",
            tags=["geometric", "simple_pattern"]
        ),

        # ===== VERBAL REASONING =====
        Question(
            id="VR-01",
            text="'Ephemeral' is to 'Permanent' as 'Gregarious' is to:",
            options=["Friendly", "Reclusive", "Talkative", "Generous"],
            correct_answer=1,
            difficulty=Difficulty.MEDIUM,
            category=CognitiveCategory.VERBAL_REASONING,
            explanation="Ephemeral (short-lived) is the opposite of Permanent. Gregarious (sociable) is the opposite of Reclusive (solitary).",
            tags=["analogy", "antonyms"]
        ),
        Question(
            id="VR-02",
            text="Which word does NOT belong: 'Elated, Jubilant, Ecstatic, Melancholy, Exuberant'?",
            options=["Elated", "Jubilant", "Melancholy", "Exuberant"],
            correct_answer=2,
            difficulty=Difficulty.EASY,
            category=CognitiveCategory.VERBAL_REASONING,
            explanation="Elated, Jubilant, Ecstatic, and Exuberant all mean extremely happy. Melancholy means sad.",
            tags=["odd_one_out", "vocabulary"]
        ),
        Question(
            id="VR-03",
            text="'The scientist's hypothesis was corroborated by subsequent experiments.' What does 'corroborated' mean?",
            options=[
                "Contradicted",
                "Supported with evidence",
                "Ignored",
                "Modified significantly"
            ],
            correct_answer=1,
            difficulty=Difficulty.MEDIUM,
            category=CognitiveCategory.VERBAL_REASONING,
            explanation="Corroborated means confirmed or supported with additional evidence or testimony.",
            tags=["vocabulary", "context_clues"]
        ),

        # ===== NUMERICAL REASONING =====
        Question(
            id="NR-01",
            text="A shirt costs $80. It's on sale for 25% off, then an additional 10% off the sale price. What's the final price?",
            options=["$52.00", "$54.00", "$56.00", "$48.00"],
            correct_answer=1,
            difficulty=Difficulty.MEDIUM,
            category=CognitiveCategory.NUMERICAL_REASONING,
            explanation="25% off $80 = $60. Then 10% off $60 = $54. Note: two successive discounts of 25% and 10% ≠ 35% off.",
            tags=["percentages", "multi_step"]
        ),
        Question(
            id="NR-02",
            text="If 5 machines take 5 minutes to make 5 widgets, how long would 100 machines take to make 100 widgets?",
            options=["100 minutes", "5 minutes", "20 minutes", "1 minute"],
            correct_answer=1,
            difficulty=Difficulty.HARD,
            category=CognitiveCategory.NUMERICAL_REASONING,
            explanation="Each machine makes 1 widget in 5 minutes. With 100 machines working simultaneously, 100 widgets take 5 minutes.",
            tags=["rate_problems", "trick_question"]
        ),
        Question(
            id="NR-03",
            text="What is 15% of 240?",
            options=["32", "36", "34", "38"],
            correct_answer=1,
            difficulty=Difficulty.VERY_EASY,
            category=CognitiveCategory.NUMERICAL_REASONING,
            explanation="15% of 240 = 0.15 × 240 = 36.",
            tags=["percentages", "basic"]
        ),
        Question(
            id="NR-04",
            text="A train travels 360 km in 4 hours. A car covers the same distance at 2/3 the speed. How long does the car take?",
            options=["5 hours", "6 hours", "7 hours", "8 hours"],
            correct_answer=1,
            difficulty=Difficulty.MEDIUM,
            category=CognitiveCategory.NUMERICAL_REASONING,
            explanation="Train speed = 90 km/h. Car speed = 60 km/h. Time = 360/60 = 6 hours.",
            tags=["speed_distance", "ratios"]
        ),

        # ===== SPATIAL REASONING =====
        Question(
            id="SR-01",
            text="If you fold a square piece of paper in half diagonally and cut a small circle in the center of the folded edge, how many holes appear when unfolded?",
            options=["1", "2", "3", "4"],
            correct_answer=0,
            difficulty=Difficulty.MEDIUM,
            category=CognitiveCategory.SPATIAL_REASONING,
            explanation="Cutting at the center of the folded edge creates a hole on the fold line. When unfolded, it's one elongated hole (or one hole centered on the fold).",
            tags=["paper_folding", "visualization"]
        ),
        Question(
            id="SR-02",
            text="A cube has 6 faces. If you paint all faces red and then cut the cube into 27 equal smaller cubes (3×3×3), how many small cubes have exactly 2 red faces?",
            options=["8", "12", "6", "4"],
            correct_answer=1,
            difficulty=Difficulty.HARD,
            category=CognitiveCategory.SPATIAL_REASONING,
            explanation="Edge cubes (not corners) have exactly 2 painted faces. A 3×3×3 cube has 12 edges, each with 1 such cube = 12 cubes.",
            tags=["3d_geometry", "cubes"]
        ),
        Question(
            id="SR-03",
            text="Which 3D shape has 5 faces, 8 edges, and 5 vertices?",
            options=["Cube", "Square Pyramid", "Triangular Prism", "Tetrahedron"],
            correct_answer=1,
            difficulty=Difficulty.EASY,
            category=CognitiveCategory.SPATIAL_REASONING,
            explanation="A square pyramid has: 1 square base + 4 triangular faces = 5 faces, 8 edges, and 5 vertices.",
            tags=["3d_shapes", "properties"]
        ),

        # ===== WORKING MEMORY =====
        Question(
            id="WM-01",
            text="Remember this sequence: 7, 3, 9, 1, 5, 8. What is the sum of the 2nd and 5th numbers?",
            options=["8", "6", "12", "10"],
            correct_answer=0,
            difficulty=Difficulty.MEDIUM,
            category=CognitiveCategory.WORKING_MEMORY,
            explanation="The sequence is 7, 3, 9, 1, 5, 8. 2nd number = 3, 5th number = 5. Sum = 3 + 5 = 8.",
            tags=["digit_span", "arithmetic"]
        ),
        Question(
            id="WM-02",
            text="In the word 'COMPUTATIONAL', what is the 5th letter from the left and the 3rd letter from the right?",
            options=["U and N", "T and N", "U and A", "T and A"],
            correct_answer=0,
            difficulty=Difficulty.HARD,
            category=CognitiveCategory.WORKING_MEMORY,
            explanation="C-O-M-P-U-T-A-T-I-O-N-A-L. 5th from left = U. 3rd from right = N (L, A, N).",
            tags=["letter_position", "dual_task"]
        ),
        Question(
            id="WM-03",
            text="If A=1, B=2, C=3, ..., Z=26, what is the value of C + A + T?",
            options=["24", "27", "22", "26"],
            correct_answer=0,
            difficulty=Difficulty.EASY,
            category=CognitiveCategory.WORKING_MEMORY,
            explanation="C=3, A=1, T=20. Sum = 3 + 1 + 20 = 24.",
            tags=["letter_value", "addition"]
        ),

        # ===== CRITICAL THINKING =====
        Question(
            id="CT-01",
            text="A study found that ice cream sales and drowning rates both increase in summer. A news headline states: 'Ice Cream Causes Drowning!' What's the flaw?",
            options=[
                "The sample size was too small",
                "Correlation is confused with causation; both are caused by hot weather",
                "The study wasn't peer-reviewed",
                "Drowning causes ice cream sales"
            ],
            correct_answer=1,
            difficulty=Difficulty.MEDIUM,
            category=CognitiveCategory.CRITICAL_THINKING,
            explanation="This is a classic correlation vs. causation error. Both variables increase due to a confounding variable (hot weather), not because one causes the other.",
            tags=["correlation_causation", "fallacy"]
        ),
        Question(
            id="CT-02",
            text="'We should ban all cars because car accidents kill people.' This argument is flawed because:",
            options=[
                "Cars don't kill people",
                "It ignores the substantial benefits of cars and doesn't consider alternatives",
                "Accidents are rare",
                "Walking is more dangerous"
            ],
            correct_answer=1,
            difficulty=Difficulty.MEDIUM,
            category=CognitiveCategory.CRITICAL_THINKING,
            explanation="This is a simplistic argument that ignores the cost-benefit analysis. Cars provide enormous utility; the argument should consider risk reduction rather than outright banning.",
            tags=["argument_analysis", "cost_benefit"]
        ),
        Question(
            id="CT-03",
            text="A company claims their supplement 'boosts IQ by 30%' based on a study of 8 participants with no control group. How reliable is this claim?",
            options=[
                "Very reliable — they measured IQ",
                "Somewhat reliable — IQ is objective",
                "Unreliable — tiny sample size, no control group, and extraordinary claim",
                "We need to try it ourselves to know"
            ],
            correct_answer=2,
            difficulty=Difficulty.HARD,
            category=CognitiveCategory.CRITICAL_THINKING,
            explanation="Multiple red flags: tiny sample (n=8), no control group (placebo effect unaccounted), and an extraordinary claim (30% IQ boost is massive). This lacks scientific rigor.",
            tags=["scientific_reasoning", "evidence_evaluation"]
        ),
        Question(
            id="CT-04",
            text="'9 out of 10 dentists recommend Brand X toothpaste.' What important question should you ask about this claim?",
            options=[
                "Which brand do the other dentists recommend?",
                "How were the dentists selected, what were the alternatives offered, and who funded the study?",
                "Is Brand X more expensive?",
                "Do dentists actually use toothpaste?"
            ],
            correct_answer=1,
            difficulty=Difficulty.VERY_HARD,
            category=CognitiveCategory.CRITICAL_THINKING,
            explanation="The methodology matters: Were dentists randomly selected? Were they choosing between Brand X and nothing, or Brand X and other brands? Industry funding creates bias.",
            tags=["advertising_claims", "methodology"]
        ),
    ]

    return questions


class QuestionBank:
    """Manages the question bank with filtering and retrieval capabilities."""

    def __init__(self):
        self.questions = get_question_bank()
        self._index = {q.id: q for q in self.questions}

    def get_by_id(self, question_id: str) -> Optional[Question]:
        """Retrieve a question by its ID."""
        return self._index.get(question_id)

    def get_by_difficulty(self, difficulty: Difficulty) -> list[Question]:
        """Get all questions of a specific difficulty."""
        return [q for q in self.questions if q.difficulty == difficulty]

    def get_by_category(self, category: CognitiveCategory) -> list[Question]:
        """Get all questions in a specific cognitive category."""
        return [q for q in self.questions if q.category == category]

    def get_filtered(
        self,
        difficulty: Optional[Difficulty] = None,
        category: Optional[CognitiveCategory] = None,
        exclude_ids: Optional[set[str]] = None
    ) -> list[Question]:
        """Get questions matching filters, excluding already-asked questions."""
        result = self.questions
        if difficulty is not None:
            result = [q for q in result if q.difficulty == difficulty]
        if category is not None:
            result = [q for q in result if q.category == category]
        if exclude_ids:
            result = [q for q in result if q.id not in exclude_ids]
        return result

    def get_difficulty_range(
        self,
        min_diff: int,
        max_diff: int,
        exclude_ids: Optional[set[str]] = None
    ) -> list[Question]:
        """Get questions within a difficulty range."""
        result = [q for q in self.questions if min_diff <= q.difficulty.value <= max_diff]
        if exclude_ids:
            result = [q for q in result if q.id not in exclude_ids]
        return result

    def get_categories(self) -> list[CognitiveCategory]:
        """Get all unique categories in the bank."""
        return list(set(q.category for q in self.questions))

    def get_stats(self) -> dict:
        """Get statistics about the question bank."""
        stats = {
            "total": len(self.questions),
            "by_difficulty": {},
            "by_category": {},
        }
        for diff in Difficulty:
            count = len(self.get_by_difficulty(diff))
            if count > 0:
                stats["by_difficulty"][str(diff)] = count
        for cat in CognitiveCategory:
            count = len(self.get_by_category(cat))
            if count > 0:
                stats["by_category"][str(cat)] = count
        return stats