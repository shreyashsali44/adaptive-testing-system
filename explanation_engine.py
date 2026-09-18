"""
Explanation Engine
Provides transparent explanations of adaptive decisions.

Author: [Candidate Name]
AI-Assisted: None. Entirely manual implementation.
"""

from user_state import UserState
from config import Difficulty, CognitiveCategory


class ExplanationEngine:
    """
    Generates human-readable explanations for all adaptive decisions.

    This module ensures the adaptive logic is "explicit and explainable"
    as required by the specification.
    """

    @staticmethod
    def explain_difficulty_change(
        previous_difficulty: Difficulty,
        new_difficulty: Difficulty,
        user_state: UserState
    ) -> str:
        """Explain why difficulty changed."""
        if new_difficulty.value > previous_difficulty.value:
            return (
                f"📈 Difficulty increased from {previous_difficulty} to {new_difficulty}. "
                f"Reason: Your recent accuracy ({user_state.recent_accuracy:.0%}) and "
                f"estimated ability ({user_state.estimated_ability:.1f}/5.0) indicate "
                f"you're ready for more challenge."
            )
        elif new_difficulty.value < previous_difficulty.value:
            return (
                f"📉 Difficulty decreased from {previous_difficulty} to {new_difficulty}. "
                f"Reason: Your recent accuracy ({user_state.recent_accuracy:.0%}) suggests "
                f"a lighter difficulty will help us better assess your capabilities."
            )
        else:
            return (
                f"➡️ Difficulty maintained at {new_difficulty}. "
                f"Reason: Your performance is well-matched to this level "
                f"(accuracy: {user_state.recent_accuracy:.0%})."
            )

    @staticmethod
    def explain_category_selection(
        category: CognitiveCategory,
        user_state: UserState,
        reason: str
    ) -> str:
        """Explain why a particular category was selected."""
        accuracy = user_state.get_category_accuracy(category)
        if accuracy is not None:
            return (
                f"🧠 Category: {category} (your accuracy: {accuracy:.0%}). "
                f"Selection reason: {reason}"
            )
        else:
            return (
                f"🧠 Category: {category} (not yet tested). "
                f"Selection reason: {reason}"
            )

    @staticmethod
    def explain_overall_strategy(user_state: UserState) -> str:
        """Provide an overall strategy explanation at the current point."""
        q_num = user_state.questions_answered

        if q_num <= 2:
            phase = "Calibration Phase"
            desc = "Establishing your baseline ability level."
        elif q_num <= 5:
            phase = "Exploration Phase"
            desc = "Testing across different cognitive categories and difficulty levels."
        elif q_num <= 8:
            phase = "Focused Assessment Phase"
            desc = "Drilling into specific areas based on your performance patterns."
        else:
            phase = "Validation Phase"
            desc = "Confirming findings and testing boundaries of your abilities."

        return f"📋 Current Strategy: {phase} — {desc}"

    @staticmethod
    def format_decision_log(user_state: UserState) -> str:
        """Format the complete decision log for review."""
        if not user_state.adaptive_decisions:
            return "No adaptive decisions recorded yet."

        lines = ["═══ ADAPTIVE DECISION LOG ═══\n"]
        for i, decision in enumerate(user_state.adaptive_decisions):
            lines.append(f"Question {i + 1}: {decision.question_id}")
            lines.append(f"  Target Difficulty: {Difficulty(decision.target_difficulty)}")
            if decision.target_category:
                lines.append(f"  Target Category: {CognitiveCategory(decision.target_category)}")
            lines.append(f"  Reasoning: {decision.reasoning}")
            if decision.factors:
                lines.append(f"  Key Factors: {decision.factors}")
            lines.append("")

        return "\n".join(lines)