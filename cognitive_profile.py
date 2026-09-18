"""
Cognitive Profile Generator
Builds a comprehensive cognitive profile from test results.

Author: [Candidate Name]
AI-Assisted: Profile structure design reviewed with AI.
Analysis algorithms and profile generation logic are manual implementations.
"""

from typing import Optional
from user_state import UserState
from scoring import ScoringEngine
from llm_integration import get_llm
from config import CognitiveCategory, Difficulty
import json


class CognitiveProfileGenerator:
    """
    Generates a comprehensive cognitive profile based on test performance.

    The profile includes:
    1. Overall cognitive assessment
    2. Per-category performance analysis
    3. Difficulty progression analysis
    4. Response pattern analysis
    5. Strengths and weaknesses
    6. Narrative summary (LLM-generated when available)
    """

    def __init__(self, user_state: UserState):
        self.state = user_state
        self.scoring = ScoringEngine()
        self.llm = get_llm()

    def generate_full_profile(self) -> dict:
        """Generate the complete cognitive profile."""
        score_breakdown = self.scoring.get_score_breakdown(self.state)

        profile = {
            "summary": self._generate_summary(score_breakdown),
            "overall_metrics": self._get_overall_metrics(score_breakdown),
            "category_analysis": self._analyze_categories(score_breakdown),
            "difficulty_progression": self._analyze_difficulty_progression(),
            "response_patterns": self._analyze_response_patterns(),
            "strengths": self._identify_strengths(score_breakdown),
            "weaknesses": self._identify_weaknesses(score_breakdown),
            "adaptive_journey": self._summarize_adaptive_journey(),
            "narrative_profile": self._generate_narrative(score_breakdown),
            "raw_score_breakdown": score_breakdown,
        }

        return profile

    def _generate_summary(self, score_breakdown: dict) -> dict:
        """Generate a concise summary of performance."""
        accuracy = score_breakdown["overall_accuracy"]

        if accuracy >= 85:
            performance_level = "Exceptional"
            description = "Outstanding performance demonstrating advanced cognitive abilities."
        elif accuracy >= 70:
            performance_level = "Strong"
            description = "Strong performance showing well-developed cognitive skills."
        elif accuracy >= 55:
            performance_level = "Competent"
            description = "Solid performance with balanced cognitive capabilities."
        elif accuracy >= 40:
            performance_level = "Developing"
            description = "Developing performance with identifiable areas for growth."
        else:
            performance_level = "Emerging"
            description = "Emerging cognitive skills with significant room for development."

        return {
            "performance_level": performance_level,
            "description": description,
            "total_score": score_breakdown["total_score"],
            "accuracy_percentage": accuracy,
            "estimated_percentile": score_breakdown["estimated_percentile"],
        }

    def _get_overall_metrics(self, score_breakdown: dict) -> dict:
        """Get overall performance metrics."""
        return {
            "questions_answered": score_breakdown["questions_answered"],
            "correct_answers": score_breakdown["correct_answers"],
            "accuracy": score_breakdown["overall_accuracy"],
            "average_response_time": score_breakdown["average_time_per_question"],
            "max_streak": score_breakdown["max_streak"],
            "final_estimated_ability": round(self.state.estimated_ability, 2),
            "difficulty_range_attempted": self._get_difficulty_range(),
        }

    def _get_difficulty_range(self) -> str:
        """Get the range of difficulties attempted."""
        if not self.state.answers:
            return "None"
        difficulties = [a.question_difficulty.value for a in self.state.answers]
        min_d = Difficulty.from_value(min(difficulties))
        max_d = Difficulty.from_value(max(difficulties))
        return f"{min_d} to {max_d}"

    def _analyze_categories(self, score_breakdown: dict) -> dict:
        """Detailed analysis of performance in each cognitive category."""
        category_scores = score_breakdown.get("category_scores", {})
        category_stats = self.state.get_category_stats()
        analysis = {}

        for cat in CognitiveCategory:
            cat_key = cat.value
            if cat_key in category_stats:
                stats = category_stats[cat_key]
                score = category_scores.get(cat_key, 0)

                # Determine level
                if stats["accuracy"] >= 0.8:
                    level = "Strong"
                elif stats["accuracy"] >= 0.5:
                    level = "Moderate"
                else:
                    level = "Developing"

                analysis[cat_key] = {
                    "name": str(cat),
                    "questions_attempted": stats["total"],
                    "correct": stats["correct"],
                    "accuracy": round(stats["accuracy"] * 100, 1),
                    "weighted_score": score,
                    "average_difficulty": stats["average_difficulty"],
                    "level": level,
                }

        return analysis

    def _analyze_difficulty_progression(self) -> dict:
        """Analyze how difficulty changed throughout the test."""
        if not self.state.answers:
            return {"progression": [], "trend": "N/A"}

        progression = []
        for i, answer in enumerate(self.state.answers):
            progression.append({
                "question_number": i + 1,
                "difficulty": answer.question_difficulty.value,
                "correct": answer.is_correct,
                "category": answer.question_category.value,
            })

        # Calculate trend
        difficulties = [a.question_difficulty.value for a in self.state.answers]
        if len(difficulties) >= 3:
            first_half = sum(difficulties[:len(difficulties)//2]) / max(1, len(difficulties)//2)
            second_half = sum(difficulties[len(difficulties)//2:]) / max(1, len(difficulties) - len(difficulties)//2)

            if second_half > first_half + 0.5:
                trend = "Ascending (questions got harder as you performed well)"
            elif second_half < first_half - 0.5:
                trend = "Descending (questions were adjusted to match your level)"
            else:
                trend = "Stable (difficulty remained relatively consistent)"
        else:
            trend = "Insufficient data for trend analysis"

        return {
            "progression": progression,
            "trend": trend,
            "starting_difficulty": difficulties[0] if difficulties else 0,
            "ending_difficulty": difficulties[-1] if difficulties else 0,
            "peak_difficulty": max(difficulties) if difficulties else 0,
        }

    def _analyze_response_patterns(self) -> dict:
        """Analyze patterns in the user's responses."""
        if not self.state.answers:
            return {}

        times = [a.time_taken for a in self.state.answers]
        correct_times = [a.time_taken for a in self.state.answers if a.is_correct]
        wrong_times = [a.time_taken for a in self.state.answers if not a.is_correct]

        patterns = {
            "average_response_time": round(sum(times) / len(times), 1),
            "fastest_response": round(min(times), 1),
            "slowest_response": round(max(times), 1),
        }

        if correct_times:
            patterns["avg_time_correct"] = round(sum(correct_times) / len(correct_times), 1)
        if wrong_times:
            patterns["avg_time_incorrect"] = round(sum(wrong_times) / len(wrong_times), 1)

        # Speed-accuracy relationship
        if correct_times and wrong_times:
            avg_correct_time = sum(correct_times) / len(correct_times)
            avg_wrong_time = sum(wrong_times) / len(wrong_times)
            if avg_correct_time < avg_wrong_time:
                patterns["speed_accuracy_note"] = "You tend to answer correct questions faster, suggesting confident knowledge."
            else:
                patterns["speed_accuracy_note"] = "You tend to spend more time on questions you get right, suggesting careful deliberation pays off."

        return patterns

    def _identify_strengths(self, score_breakdown: dict) -> list[str]:
        """Identify cognitive strengths."""
        strengths = []
        category_scores = score_breakdown.get("category_scores", {})

        # High accuracy categories
        for cat_key, score in category_scores.items():
            if score >= 60:
                cat_name = cat_key.replace('_', ' ').title()
                strengths.append(f"Strong {cat_name} skills (score: {score:.0f})")

        # Overall performance
        if score_breakdown["overall_accuracy"] >= 70:
            strengths.append("High overall accuracy across the assessment")

        if score_breakdown.get("max_streak", 0) >= 3:
            strengths.append(f"Impressive consistency streak of {score_breakdown['max_streak']} correct answers")

        if score_breakdown.get("average_time_per_question", 60) < 15:
            strengths.append("Quick, efficient problem-solving speed")

        if not strengths:
            strengths.append("Willingness to engage with challenging cognitive tasks")

        return strengths

    def _identify_weaknesses(self, score_breakdown: dict) -> list[str]:
        """Identify areas for improvement."""
        weaknesses = []
        category_scores = score_breakdown.get("category_scores", {})

        # Low accuracy categories
        for cat_key, score in category_scores.items():
            if score < 30:
                cat_name = cat_key.replace('_', ' ').title()
                weaknesses.append(f"{cat_name} could benefit from practice (score: {score:.0f})")

        # Overall accuracy
        if score_breakdown["overall_accuracy"] < 50:
            weaknesses.append("Overall accuracy suggests foundational skills need strengthening")

        if score_breakdown.get("average_time_per_question", 0) > 40:
            weaknesses.append("Response time suggests difficulty with time-pressured tasks")

        if not weaknesses:
            weaknesses.append("No significant weaknesses identified in this assessment")

        return weaknesses

    def _summarize_adaptive_journey(self) -> list[dict]:
        """Summarize the adaptive decisions made during the test."""
        journey = []
        for i, decision in enumerate(self.state.adaptive_decisions):
            journey.append({
                "step": i + 1,
                "question_selected": decision.question_id,
                "target_difficulty": str(Difficulty(decision.target_difficulty)),
                "reasoning_summary": decision.reasoning[:150] + "..." if len(decision.reasoning) > 150 else decision.reasoning,
            })
        return journey

    def _generate_narrative(self, score_breakdown: dict) -> str:
        """Generate a narrative profile using LLM or fallback."""
        user_summary = self.state.get_summary_for_llm()
        return self.llm.generate_cognitive_profile(user_summary, score_breakdown)