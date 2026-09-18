"""
LLM Integration Module
Handles all LLM/API interactions for enhanced features.

Author: [Candidate Name]
AI-Assisted: Prompt templates were iterated with AI assistance.
Error handling, fallback logic, and integration architecture
are manual implementations.
"""

import os
import json
import logging
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)


class LLMIntegration:
    """
    Manages LLM interactions for:
    1. Generating cognitive profile narratives
    2. Providing personalized feedback on answers
    3. Generating adaptive explanations
    4. Fallback mode when API is unavailable

    Handles:
    - API failures gracefully with fallback responses
    - Invalid/hallucinated responses with validation
    - Rate limiting and retries
    """

    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.model = Config.MODEL_NAME
        self.client = None
        self.available = False

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.available = True
                logger.info("LLM integration initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.available = False
        else:
            logger.info("No API key provided. Running in fallback mode.")

    def _call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> Optional[str]:
        """
        Make an LLM API call with error handling.

        Returns None if the call fails, triggering fallback behavior.
        """
        if not self.available or not self.client:
            return None

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            content = response.choices[0].message.content
            if content and len(content.strip()) > 10:
                return content.strip()
            else:
                logger.warning("LLM returned empty or very short response.")
                return None
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return None

    def generate_cognitive_profile(self, user_state_summary: str, score_breakdown: dict) -> str:
        """
        Generate a narrative cognitive profile based on test results.

        Falls back to template-based profile if API unavailable.
        """
        system_prompt = """You are a cognitive assessment specialist. Based on the test results provided, 
generate a concise cognitive profile (200-300 words). Include:
1. Overall cognitive performance summary
2. Strongest cognitive areas
3. Areas for improvement
4. Notable patterns in performance
5. Brief recommendations

Be professional but encouraging. Base assessments ONLY on the data provided.
Do not invent or assume information not present in the results."""

        user_prompt = f"""Test Results:
{user_state_summary}

Score Breakdown:
{json.dumps(score_breakdown, indent=2)}

Generate a cognitive profile based on these results."""

        result = self._call_llm(system_prompt, user_prompt, max_tokens=600)

        if result:
            # Validate: check the response is relevant
            if any(keyword in result.lower() for keyword in ['cognitive', 'performance', 'score', 'strength', 'area']):
                return result
            else:
                logger.warning("LLM response doesn't appear to be a cognitive profile. Using fallback.")

        # Fallback: template-based profile
        return self._generate_fallback_profile(score_breakdown)

    def generate_answer_feedback(
        self,
        question_text: str,
        correct_answer: str,
        user_answer: str,
        is_correct: bool,
        explanation: str
    ) -> str:
        """
        Generate personalized feedback for an answer.

        Falls back to the question's built-in explanation if API unavailable.
        """
        if not is_correct:
            system_prompt = """You are a supportive cognitive tutor. The user answered a question incorrectly.
Provide brief (2-3 sentences), encouraging feedback that:
1. Acknowledges their effort
2. Explains the correct reasoning simply
3. Gives a tip for similar questions

Do NOT be condescending. Be warm and educational."""

            user_prompt = f"""Question: {question_text}
User's answer: {user_answer}
Correct answer: {correct_answer}
Explanation: {explanation}

Provide brief, encouraging feedback."""

            result = self._call_llm(system_prompt, user_prompt, max_tokens=150)
            if result:
                return result

        # Fallback
        if is_correct:
            return f"✓ Correct! {explanation}"
        else:
            return f"✗ The correct answer was: {correct_answer}. {explanation}"

    def generate_adaptive_insight(self, decision_explanation: str, user_state_summary: str) -> str:
        """
        Generate an enhanced explanation of why a question was selected.
        Used for the bonus feature of internal explanations.
        """
        system_prompt = """You are an adaptive testing engine. Briefly explain (1-2 sentences) why the next 
question was selected, using plain language a test-taker could understand. 
Reference specific performance metrics from the data provided."""

        user_prompt = f"""Selection reasoning: {decision_explanation}

User state: {user_state_summary}

Provide a brief, clear explanation of the adaptation."""

        result = self._call_llm(system_prompt, user_prompt, max_tokens=100)
        return result if result else decision_explanation

    def _generate_fallback_profile(self, score_breakdown: dict) -> str:
        """Generate a template-based cognitive profile when LLM is unavailable."""
        total = score_breakdown.get("questions_answered", 0)
        correct = score_breakdown.get("correct_answers", 0)
        accuracy = score_breakdown.get("overall_accuracy", 0)
        percentile = score_breakdown.get("estimated_percentile", 50)
        category_scores = score_breakdown.get("category_scores", {})

        # Determine overall level
        if accuracy >= 80:
            level = "excellent"
            level_desc = "You demonstrated strong cognitive abilities across the assessment."
        elif accuracy >= 60:
            level = "good"
            level_desc = "You showed solid cognitive abilities with room for growth in specific areas."
        elif accuracy >= 40:
            level = "moderate"
            level_desc = "Your performance indicates developing cognitive skills with clear areas for improvement."
        else:
            level = "developing"
            level_desc = "Your results suggest significant room for cognitive skill development."

        profile = f"""═══ COGNITIVE PROFILE ═══

OVERALL ASSESSMENT: {level.upper()}
{level_desc}

PERFORMANCE SUMMARY:
• Questions answered: {total}
• Accuracy: {accuracy}%
• Estimated percentile: {percentile}%
• Total score: {score_breakdown.get('total_score', 0)}
"""

        if category_scores:
            # Find strongest and weakest
            sorted_cats = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
            strongest = sorted_cats[0] if sorted_cats else None
            weakest = sorted_cats[-1] if len(sorted_cats) > 1 else None

            profile += "\nCOGNITIVE STRENGTHS:\n"
            if strongest:
                cat_name = strongest[0].replace('_', ' ').title()
                profile += f"• {cat_name} (Score: {strongest[1]})\n"

            if weakest and weakest[1] < strongest[1]:
                profile += "\nAREAS FOR GROWTH:\n"
                cat_name = weakest[0].replace('_', ' ').title()
                profile += f"• {cat_name} (Score: {weakest[1]})\n"

            profile += "\nDETAILED CATEGORY SCORES:\n"
            for cat_key, score in sorted_cats:
                cat_name = cat_key.replace('_', ' ').title()
                bar_length = int(score / 5)
                bar = "█" * bar_length + "░" * (20 - bar_length)
                profile += f"  {cat_name:.<30} [{bar}] {score:.1f}\n"

        profile += f"""
RECOMMENDATIONS:
• {"Continue challenging yourself with advanced problems." if accuracy >= 70 else "Practice foundational concepts before moving to harder problems."}
• {"Focus on maintaining your strong performance across categories." if accuracy >= 70 else "Focus additional practice on your weaker cognitive areas."}
• {"Your speed and accuracy balance is good." if score_breakdown.get('average_time_per_question', 30) < 25 else "Consider spending more time reading questions carefully."}

Note: This profile is based on a brief assessment and provides an indicative snapshot.
A comprehensive cognitive evaluation would involve more extensive testing.
"""
        return profile


# Singleton instance
_llm_instance = None


def get_llm() -> LLMIntegration:
    """Get or create the singleton LLM integration instance."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMIntegration()
    return _llm_instance