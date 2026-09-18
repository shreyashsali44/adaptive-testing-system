"""
Adaptive Question Selection Engine
Core adaptive logic that selects the next question based on user state.

Author: [Candidate Name]
AI-Assisted: The overall algorithm structure was designed manually.
AI was consulted for reviewing the weight balancing approach.
The selection algorithm, scoring heuristics, and decision logic
are entirely manual implementations.
"""

import random
from typing import Optional
from config import Config, Difficulty, CognitiveCategory
from question_bank import QuestionBank, Question
from user_state import UserState, AdaptiveDecision


class AdaptiveEngine:
    """
    Selects the next question adaptively based on user performance.

    The selection algorithm uses a multi-factor scoring approach:

    1. DIFFICULTY MATCHING (50% weight):
       - Targets a difficulty level based on estimated ability
       - Strong performance → harder questions
       - Weak performance → easier/diagnostic questions

    2. CATEGORY DIVERSITY (30% weight):
       - Prefers under-tested categories for breadth
       - May target weak categories for diagnostic depth

    3. RECENCY ADJUSTMENT (20% weight):
       - Recent performance weighted more than historical
       - Streak detection for rapid difficulty changes

    Each candidate question receives a composite score, and the
    highest-scoring question is selected (with controlled randomness).
    """

    def __init__(self, question_bank: QuestionBank):
        self.bank = question_bank
        self.all_categories = question_bank.get_categories()

    def select_next_question(self, user_state: UserState) -> tuple[Question, str]:
        """
        Select the next question based on user state.

        Returns:
            Tuple of (selected_question, explanation_string)
        """
        # If this is the first question, start with medium difficulty
        if user_state.questions_answered == 0:
            return self._select_initial_question(user_state)

        # Determine target difficulty
        target_difficulty = self._calculate_target_difficulty(user_state)

        # Determine target category (or None for any)
        target_category = self._select_target_category(user_state)

        # Get candidate questions
        candidates = self._get_candidates(user_state, target_difficulty, target_category)

        # Score and rank candidates
        if not candidates:
            # Fallback: get ANY available question
            candidates = self.bank.get_filtered(exclude_ids=user_state.asked_question_ids)
            if not candidates:
                raise RuntimeError("No more questions available in the bank!")

        scored_candidates = self._score_candidates(candidates, user_state, target_difficulty, target_category)

        # Select the best question (with slight randomness to avoid predictability)
        selected = self._select_from_scored(scored_candidates)

        # Generate explanation
        explanation = self._generate_explanation(
            selected, user_state, target_difficulty, target_category
        )

        # Record the adaptive decision
        decision = AdaptiveDecision(
            question_id=selected.id,
            target_difficulty=target_difficulty,
            target_category=target_category,
            reasoning=explanation,
            factors={
                "estimated_ability": round(user_state.estimated_ability, 2),
                "recent_accuracy": round(user_state.recent_accuracy, 2),
                "overall_accuracy": round(user_state.overall_accuracy, 2),
                "consecutive_correct": user_state.consecutive_correct,
                "consecutive_wrong": user_state.consecutive_wrong,
                "questions_answered": user_state.questions_answered,
            }
        )
        user_state.record_adaptive_decision(decision)

        # Update current difficulty in user state
        user_state.current_difficulty = target_difficulty

        return selected, explanation

    def _select_initial_question(self, user_state: UserState) -> tuple[Question, str]:
        """Select the first question: medium difficulty, random category."""
        candidates = self.bank.get_by_difficulty(Difficulty.MEDIUM)
        if not candidates:
            candidates = self.bank.get_by_difficulty(Difficulty.EASY)

        selected = random.choice(candidates)
        explanation = (
            f"First question: Starting at {Difficulty.MEDIUM} difficulty "
            f"in {selected.category} to establish baseline performance."
        )

        decision = AdaptiveDecision(
            question_id=selected.id,
            target_difficulty=Difficulty.MEDIUM,
            target_category=None,
            reasoning=explanation,
            factors={"reason": "initial_question"}
        )
        user_state.record_adaptive_decision(decision)
        user_state.current_difficulty = Difficulty.MEDIUM

        return selected, explanation

    def _calculate_target_difficulty(self, user_state: UserState) -> Difficulty:
        """
        Calculate the target difficulty for the next question.

        This is the core adaptive logic:
        - Uses estimated ability as the primary signal
        - Adjusts based on recent performance trends
        - Applies streak-based rapid adjustments
        """
        # Base target from estimated ability
        base_target = round(user_state.estimated_ability)

        # Recent performance adjustment
        recent_acc = user_state.recent_accuracy

        if recent_acc >= Config.DIFFICULTY_INCREASE_THRESHOLD:
            # Performing well recently → push harder
            adjustment = 1
        elif recent_acc <= Config.DIFFICULTY_DECREASE_THRESHOLD:
            # Struggling recently → ease off
            adjustment = -1
        else:
            # Moderate performance → stay around current level
            adjustment = 0

        # Streak-based rapid adjustment
        if user_state.consecutive_correct >= Config.CONSECUTIVE_CORRECT_BOOST:
            adjustment += 1  # Extra push for sustained excellence
        elif user_state.consecutive_wrong >= Config.CONSECUTIVE_WRONG_DROP:
            adjustment -= 1  # Extra help for sustained struggle

        # Calculate final target
        target_value = base_target + adjustment
        target_value = max(1, min(5, target_value))

        return Difficulty.from_value(target_value)

    def _select_target_category(self, user_state: UserState) -> Optional[CognitiveCategory]:
        """
        Decide which cognitive category to target next.

        Strategy:
        1. Every 3rd question: target the least-tested category (breadth)
        2. If user is struggling: target their weakest category (diagnosis)
        3. Otherwise: weighted random based on coverage gaps
        """
        q_num = user_state.questions_answered + 1

        # Every 3rd question: ensure category diversity
        if q_num % 3 == 0:
            least_tested = user_state.get_least_tested_categories(self.all_categories)
            if least_tested:
                return random.choice(least_tested)

        # If on a losing streak: probe weak areas
        if user_state.consecutive_wrong >= 2:
            weak_cats = user_state.get_weakest_categories()
            if weak_cats:
                return random.choice(weak_cats)

        # If on a winning streak: test strong areas at higher difficulty
        if user_state.consecutive_correct >= 3:
            strong_cats = user_state.get_strongest_categories()
            if strong_cats:
                return random.choice(strong_cats)

        # Default: slight preference for untested categories
        category_counts = {}
        for cat in self.all_categories:
            count = sum(1 for a in user_state.answers if a.question_category == cat)
            category_counts[cat] = count

        # Weight inversely by frequency
        if category_counts:
            min_count = min(category_counts.values())
            underrepresented = [cat for cat, count in category_counts.items() if count <= min_count]
            if underrepresented and random.random() < 0.5:
                return random.choice(underrepresented)

        return None  # No specific category preference

    def _get_candidates(
        self,
        user_state: UserState,
        target_difficulty: Difficulty,
        target_category: Optional[CognitiveCategory]
    ) -> list[Question]:
        """
        Get candidate questions, expanding search if needed.

        Strategy: Start narrow (exact match), then progressively broaden.
        """
        exclude = user_state.asked_question_ids

        # Try exact match first
        candidates = self.bank.get_filtered(
            difficulty=target_difficulty,
            category=target_category,
            exclude_ids=exclude
        )

        if candidates:
            return candidates

        # Broaden: same difficulty, any category
        candidates = self.bank.get_filtered(
            difficulty=target_difficulty,
            exclude_ids=exclude
        )

        if candidates:
            return candidates

        # Broaden more: adjacent difficulty levels
        target_val = target_difficulty.value
        candidates = self.bank.get_difficulty_range(
            max(1, target_val - 1),
            min(5, target_val + 1),
            exclude_ids=exclude
        )

        if candidates:
            return candidates

        # Final fallback: any available question
        return self.bank.get_filtered(exclude_ids=exclude)

    def _score_candidates(
        self,
        candidates: list[Question],
        user_state: UserState,
        target_difficulty: Difficulty,
        target_category: Optional[CognitiveCategory]
    ) -> list[tuple[Question, float]]:
        """
        Score each candidate question based on multiple factors.

        Returns list of (question, score) tuples, sorted by score descending.
        """
        scored = []

        for question in candidates:
            score = 0.0

            # Factor 1: Difficulty match (50% weight)
            diff_distance = abs(question.difficulty.value - target_difficulty.value)
            difficulty_score = max(0, 1.0 - diff_distance * 0.3)
            score += difficulty_score * Config.PERFORMANCE_WEIGHT * 100

            # Factor 2: Category diversity (30% weight)
            cat_count = sum(1 for a in user_state.answers if a.question_category == question.category)
            total_asked = max(1, user_state.questions_answered)
            category_frequency = cat_count / total_asked
            diversity_score = 1.0 - category_frequency
            score += diversity_score * Config.CATEGORY_ROTATION_WEIGHT * 100

            # Factor 3: Category match bonus (if targeting specific category)
            if target_category and question.category == target_category:
                score += 15

            # Factor 4: Diagnostic value for weak areas
            cat_accuracy = user_state.get_category_accuracy(question.category)
            if cat_accuracy is not None and cat_accuracy < 0.5:
                # Bonus for testing weak categories
                score += 10 * (1 - cat_accuracy)

            # Factor 5: Small random factor for variety
            score += random.uniform(0, 5)

            scored.append((question, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def _select_from_scored(self, scored_candidates: list[tuple[Question, float]]) -> Question:
        """
        Select from top-scored candidates with slight randomness.

        Takes top 3 candidates and does weighted random selection
        to avoid being completely predictable.
        """
        if len(scored_candidates) == 1:
            return scored_candidates[0][0]

        # Take top 3 (or fewer)
        top_n = scored_candidates[:min(3, len(scored_candidates))]

        # Weighted selection by score
        total_score = sum(score for _, score in top_n)
        if total_score == 0:
            return random.choice([q for q, _ in top_n])

        weights = [score / total_score for _, score in top_n]
        questions = [q for q, _ in top_n]

        selected = random.choices(questions, weights=weights, k=1)[0]
        return selected

    def _generate_explanation(
        self,
        selected: Question,
        user_state: UserState,
        target_difficulty: Difficulty,
        target_category: Optional[CognitiveCategory]
    ) -> str:
        """
        Generate a human-readable explanation of why this question was selected.

        This fulfills the bonus requirement for internal explanations.
        """
        parts = []

        # Performance context
        if user_state.questions_answered == 0:
            parts.append("Starting test with baseline assessment.")
        else:
            last_answer = user_state.answers[-1]
            if last_answer.is_correct:
                parts.append(f"Previous answer was CORRECT (difficulty: {last_answer.question_difficulty}).")
            else:
                parts.append(f"Previous answer was INCORRECT (difficulty: {last_answer.question_difficulty}).")

        # Difficulty reasoning
        if target_difficulty.value > user_state.current_difficulty.value:
            parts.append(
                f"Increasing difficulty to {target_difficulty} "
                f"(ability estimate: {user_state.estimated_ability:.1f}/5.0, "
                f"recent accuracy: {user_state.recent_accuracy:.0%})."
            )
        elif target_difficulty.value < user_state.current_difficulty.value:
            parts.append(
                f"Decreasing difficulty to {target_difficulty} "
                f"to provide diagnostic/supportive assessment "
                f"(recent accuracy: {user_state.recent_accuracy:.0%})."
            )
        else:
            parts.append(
                f"Maintaining difficulty at {target_difficulty} "
                f"(stable performance)."
            )

        # Category reasoning
        if target_category:
            cat_accuracy = user_state.get_category_accuracy(target_category)
            if cat_accuracy is not None and cat_accuracy < 0.5:
                parts.append(f"Targeting {target_category} (weak area, accuracy: {cat_accuracy:.0%}).")
            else:
                parts.append(f"Targeting {target_category} for category coverage.")
        else:
            parts.append(f"Selected category: {selected.category}.")

        # Streak info
        if user_state.consecutive_correct >= 2:
            parts.append(f"Streak of {user_state.consecutive_correct} correct → pushing boundaries.")
        elif user_state.consecutive_wrong >= 2:
            parts.append(f"Streak of {user_state.consecutive_wrong} wrong → providing support.")

        return " ".join(parts)