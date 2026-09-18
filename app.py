"""
Streamlit Web Interface for the Adaptive Testing System
Provides a modern, interactive web-based testing experience.

Author: [Candidate Name]
AI-Assisted: Streamlit layout patterns referenced from documentation.
Core logic integration and state management are manual implementations.
"""

import streamlit as st
import time
import json
from test_runner import TestSession
from config import Config
from question_bank import QuestionBank


def init_session_state():
    """Initialize Streamlit session state."""
    if 'test_session' not in st.session_state:
        st.session_state.test_session = None
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    if 'test_started' not in st.session_state:
        st.session_state.test_started = False
    if 'test_complete' not in st.session_state:
        st.session_state.test_complete = False
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'last_result' not in st.session_state:
        st.session_state.last_result = None
    if 'show_result' not in st.session_state:
        st.session_state.show_result = False
    if 'question_start_time' not in st.session_state:
        st.session_state.question_start_time = None


def start_test(user_id: str, num_questions: int):
    """Start a new test session."""
    st.session_state.test_session = TestSession(user_id=user_id, max_questions=num_questions)
    st.session_state.test_started = True
    st.session_state.test_complete = False
    st.session_state.results = None
    st.session_state.last_result = None
    st.session_state.show_result = False
    load_next_question()


def load_next_question():
    """Load the next question."""
    session = st.session_state.test_session
    question_data = session.get_next_question()
    if question_data is None:
        st.session_state.test_complete = True
        st.session_state.results = session.get_final_results()
    else:
        st.session_state.current_question = question_data
        st.session_state.show_result = False
        st.session_state.last_result = None
        st.session_state.question_start_time = time.time()


def submit_answer(selected_index: int, confidence: str):
    """Submit an answer."""
    session = st.session_state.test_session
    result = session.submit_answer(selected_index, confidence=confidence)
    st.session_state.last_result = result
    st.session_state.show_result = True
    if result['is_test_complete']:
        st.session_state.test_complete = True
        st.session_state.results = session.get_final_results()


def render_welcome():
    """Render the welcome/start screen."""
    st.markdown("""
    # 🧠 AI-Powered Adaptive Cognitive Assessment

    Welcome to the **Adaptive Testing System**! This assessment uses AI to dynamically 
    adjust questions based on your performance.

    ### How it works:
    - ✅ **Strong performance** → More challenging questions
    - 📊 **Struggling** → Diagnostic questions to find your level
    - 🔄 **Multiple categories** tested for a complete cognitive profile
    - 🤖 **AI explains** why each question was selected

    ### Categories:
    """)

    cols = st.columns(4)
    categories = [
        "🔢 Numerical", "🧩 Pattern Recognition",
        "📝 Verbal", "🔍 Logical Reasoning",
        "🎯 Critical Thinking", "📐 Spatial",
        "🧠 Working Memory", ""
    ]
    for i, cat in enumerate(categories):
        if cat:
            cols[i % 4].info(cat)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        user_id = st.text_input("Your Name/ID", value="user", key="user_id_input")
    with col2:
        num_questions = st.slider("Number of Questions", min_value=5, max_value=15, value=10)

    # Show question bank stats
    bank = QuestionBank()
    stats = bank.get_stats()
    with st.expander("📊 Question Bank Info"):
        st.write(f"Total questions available: {stats['total']}")
        st.write("**By Difficulty:**")
        for diff, count in stats['by_difficulty'].items():
            st.write(f"  - {diff}: {count} questions")
        st.write("**By Category:**")
        for cat, count in stats['by_category'].items():
            st.write(f"  - {cat}: {count} questions")

    if st.button("🚀 Start Assessment", type="primary", use_container_width=True):
        start_test(user_id, num_questions)
        st.rerun()


def render_question():
    """Render the current question."""
    q = st.session_state.current_question
    session = st.session_state.test_session

    # Progress bar
    progress = session.get_progress()
    st.progress(progress['progress_percentage'] / 100)

    # Header with stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Question", f"{q['question_number']}/{q['total_questions']}")
    col2.metric("Score", q['current_score'])
    col3.metric("Ability", f"{q['estimated_ability']}/5.0")
    col4.metric("Difficulty", q['difficulty'])

    st.markdown("---")

    # Adaptive explanation (bonus feature)
    with st.expander("🤖 Why was this question selected?", expanded=False):
        st.info(q['adaptive_explanation'])
        st.caption(q['strategy'])

    # Question
    st.markdown(f"### {q['text']}")
    st.caption(f"Category: {q['category']} | Difficulty: {q['difficulty']}")

    # Options
    selected = st.radio(
        "Select your answer:",
        options=q['options'],
        key=f"answer_{q['question_id']}",
        index=None
    )

    # Confidence
    confidence = st.select_slider(
        "How confident are you?",
        options=["very_low", "low", "medium", "high", "very_high"],
        value="medium",
        key=f"confidence_{q['question_id']}"
    )

    # Show elapsed time
    if st.session_state.question_start_time:
        elapsed = time.time() - st.session_state.question_start_time
        st.caption(f"⏱️ Time elapsed: {elapsed:.0f}s")

    # Submit button
    if st.button("Submit Answer", type="primary", disabled=selected is None, use_container_width=True):
        if selected is not None:
            selected_index = q['options'].index(selected)
            submit_answer(selected_index, confidence)
            st.rerun()


def render_result():
    """Render the answer result."""
    result = st.session_state.last_result
    q = st.session_state.current_question

    if result['is_correct']:
        st.success(f"✅ **Correct!** +{result['score_earned']} points")
    else:
        st.error(f"❌ **Incorrect.** The correct answer was: {result['correct_answer_text']}")

    # Feedback
    st.markdown(f"**Feedback:** {result['feedback']}")

    # Explanation
    with st.expander("📖 Detailed Explanation"):
        st.write(result['explanation'])

    # Stats
    stats = result['current_stats']
    cols = st.columns(4)
    cols[0].metric("Accuracy", f"{stats['accuracy']}%")
    cols[1].metric("Ability", f"{stats['estimated_ability']}/5.0")
    cols[2].metric("Total Score", result['total_score'])
    cols[3].metric("Time", f"{result['time_taken']}s")

    # Difficulty explanation
    if result.get('difficulty_explanation'):
        st.info(result['difficulty_explanation'])

    st.markdown("---")

    if result['is_test_complete']:
        if st.button("📊 View Results", type="primary", use_container_width=True):
            st.session_state.test_complete = True
            st.rerun()
    else:
        if st.button("➡️ Next Question", type="primary", use_container_width=True):
            load_next_question()
            st.rerun()


def render_results():
    """Render the final results and cognitive profile."""
    results = st.session_state.results
    profile = results['profile']
    summary = profile['summary']

    st.markdown("# 🏆 Assessment Complete!")
    st.markdown("---")

    # Summary
    st.markdown(f"## Overall: **{summary['performance_level']}**")
    st.markdown(summary['description'])

    cols = st.columns(3)
    cols[0].metric("Total Score", summary['total_score'])
    cols[1].metric("Accuracy", f"{summary['accuracy_percentage']}%")
    cols[2].metric("Percentile", f"{summary['estimated_percentile']}%")

    st.markdown("---")

    # Category Analysis
    st.markdown("## 📋 Category Performance")
    cat_analysis = profile.get('category_analysis', {})
    if cat_analysis:
        for cat_key, data in cat_analysis.items():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.progress(min(data['accuracy'] / 100, 1.0))
                st.caption(f"{data['name']}: {data['accuracy']}% ({data['correct']}/{data['questions_attempted']})")
            with col2:
                level_colors = {"Strong": "🟢", "Moderate": "🟡", "Developing": "🔴"}
                st.markdown(f"{level_colors.get(data['level'], '⚪')} {data['level']}")
            with col3:
                st.caption(f"Avg Diff: {data['average_difficulty']:.1f}")

    st.markdown("---")

    # Difficulty Progression
    st.markdown("## 📈 Difficulty Progression")
    diff_prog = profile.get('difficulty_progression', {})
    if diff_prog.get('progression'):
        st.caption(f"**Trend:** {diff_prog.get('trend', 'N/A')}")

        # Chart data
        chart_data = {
            "Question": [p['question_number'] for p in diff_prog['progression']],
            "Difficulty": [p['difficulty'] for p in diff_prog['progression']],
        }
        st.line_chart(chart_data, x="Question", y="Difficulty")

    # Strengths & Weaknesses
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 💪 Strengths")
        for s in profile.get('strengths', []):
            st.markdown(f"- {s}")
    with col2:
        st.markdown("### 🎯 Areas for Growth")
        for w in profile.get('weaknesses', []):
            st.markdown(f"- {w}")

    st.markdown("---")

    # Response Patterns
    patterns = profile.get('response_patterns', {})
    if patterns:
        st.markdown("### ⏱️ Response Patterns")
        pcols = st.columns(3)
        pcols[0].metric("Avg Time", f"{patterns.get('average_response_time', 0)}s")
        pcols[1].metric("Fastest", f"{patterns.get('fastest_response', 0)}s")
        pcols[2].metric("Slowest", f"{patterns.get('slowest_response', 0)}s")
        if patterns.get('speed_accuracy_note'):
            st.info(patterns['speed_accuracy_note'])

    st.markdown("---")

    # Narrative Profile
    narrative = profile.get('narrative_profile', '')
    if narrative:
        st.markdown("### 📝 Detailed Cognitive Profile")
        st.markdown(narrative)

    # Adaptive Journey
    with st.expander("🔄 Adaptive Decision Log"):
        journey = profile.get('adaptive_journey', [])
        for step in journey:
            st.markdown(f"**Step {step['step']}:** Question `{step['question_selected']}` "
                        f"(Target: {step['target_difficulty']})")
            st.caption(step['reasoning_summary'])
            st.markdown("---")

    # Full Decision Log
    with st.expander("📋 Full Technical Decision Log"):
        st.text(results.get('decision_log', 'No log available'))

    # Raw Data Download
    with st.expander("💾 Download Raw Data"):
        session_data = results.get('session_data', {})
        st.download_button(
            "Download Session Data (JSON)",
            data=json.dumps(session_data, indent=2, default=str),
            file_name="cognitive_assessment_results.json",
            mime="application/json"
        )

    st.markdown("---")
    if st.button("🔄 Take Another Test", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="AI Adaptive Cognitive Assessment",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    init_session_state()

    # Sidebar with info
    with st.sidebar:
        st.markdown("## ℹ️ System Info")
        warnings = Config.validate()
        if warnings:
            for w in warnings:
                st.warning(w)
        else:
            st.success("All systems operational")

        st.markdown("---")
        st.markdown("### 🏗️ Architecture")
        st.caption("""
        - **Adaptive Engine**: Multi-factor question selection
        - **State Manager**: Persistent user state tracking
        - **Scoring Engine**: Difficulty-weighted scoring
        - **LLM Integration**: AI-powered feedback & profiles
        - **Cognitive Profiler**: Comprehensive result analysis
        """)

        if st.session_state.test_started and not st.session_state.test_complete:
            session = st.session_state.test_session
            if session:
                progress = session.get_progress()
                st.markdown("### 📊 Current Progress")
                st.progress(progress['progress_percentage'] / 100)
                st.write(f"Questions: {progress['questions_answered']}/{progress['total_questions']}")
                st.write(f"Score: {progress['total_score']}")
                st.write(f"Accuracy: {progress['accuracy']}%")

    # Main content routing
    if not st.session_state.test_started:
        render_welcome()
    elif st.session_state.test_complete:
        render_results()
    elif st.session_state.show_result:
        render_result()
    else:
        render_question()


if __name__ == "__main__":
    main()