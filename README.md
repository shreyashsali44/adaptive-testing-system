# 🧠 AI-Powered Adaptive Cognitive Assessment System

An intelligent testing platform that dynamically adjusts question difficulty and category based on real-time user performance analysis. Built with Python, featuring LLM integration for enhanced feedback and cognitive profiling.

## 📋 Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [Adaptive Logic Explained](#adaptive-logic-explained)
- [Project Structure](#project-structure)
- [AI Tool Usage Disclosure](#ai-tool-usage-disclosure)
- [Testing](#testing)
- [API Documentation](#api-documentation)

## 🎯 Overview

This system implements an adaptive testing engine where:
- **Strong performance → harder questions** to challenge the user
- **Weak performance → easier/diagnostic questions** to find the user's level
- **Multiple cognitive categories** are tested for a complete profile
- **Every question selection is explainable** — the system tells you WHY it chose each question
- **LLM integration** provides personalized feedback and narrative cognitive profiles

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                  UI Layer                        │
│  (Streamlit Web App / CLI / FastAPI)             │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│              Test Runner (Orchestrator)           │
│  Coordinates all components, manages test flow   │
└──┬────────┬────────┬────────┬────────┬──────────┘
   │        │        │        │        │
┌──▼──┐ ┌──▼──┐ ┌──▼───┐ ┌──▼──┐ ┌──▼──────────┐
│Adapt│ │User │ │Score │ │Quest│ │LLM           │
│Engn │ │State│ │Engn  │ │Bank │ │Integration   │
│     │ │     │ │      │ │     │ │              │
│Multi│ │Per- │ │Diff  │ │25   │ │GPT-4o-mini   │
│factr│ │sist │ │weight│ │ques │ │w/ fallback   │
│selct│ │track│ │score │ │7cat │ │              │
└─────┘ └─────┘ └──────┘ └─────┘ └──────────────┘
   │                                    │
┌──▼────────────────────────────────────▼─────────┐
│         Cognitive Profile Generator              │
│  + Explanation Engine                            │
└─────────────────────────────────────────────────┘
```

### Core Components:

1. **Adaptive Engine** (`adaptive_engine.py`): Multi-factor question selection using difficulty matching (50%), category diversity (30%), and recency adjustment (20%)

2. **User State** (`user_state.py`): Comprehensive state tracking with per-category accuracy, streak detection, estimated ability via exponential moving average

3. **Scoring Engine** (`scoring.py`): Difficulty-weighted scoring with speed bonuses and streak multipliers

4. **Question Bank** (`question_bank.py`): 25 questions across 7 cognitive categories and 5 difficulty levels

5. **LLM Integration** (`llm_integration.py`): OpenAI GPT integration for narrative profiles and personalized feedback, with full fallback mode

6. **Cognitive Profiler** (`cognitive_profile.py`): Comprehensive analysis including strengths, weaknesses, difficulty progression, and response patterns

## ✨ Features

### Core Features
- ✅ 25-question bank across 7 cognitive categories
- ✅ 5 difficulty levels (Very Easy → Very Hard)
- ✅ Persistent user state throughout the test
- ✅ Adaptive question selection with multi-factor scoring
- ✅ Difficulty-weighted scoring with bonuses
- ✅ LLM-powered cognitive profile generation
- ✅ Comprehensive final cognitive profile

### Bonus Features
- ✅ Internal explanation for every question selection
- ✅ Multiple interfaces (Web UI, CLI, REST API)
- ✅ Confidence tracking per question
- ✅ Speed-accuracy analysis
- ✅ Difficulty progression visualization
- ✅ Downloadable raw data
- ✅ Full adaptive decision log
- ✅ Graceful API failure handling with fallback mode

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- (Optional) OpenAI API key for LLM features

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/adaptive-testing-system.git
cd adaptive-testing-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your OpenAI API key (optional)

# Create logs directory
mkdir -p logs
```

## 🎮 Usage

### Option 1: Streamlit Web App (Recommended)
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

### Option 2: Command Line Interface
```bash
python main.py
```

### Option 3: REST API
```bash
# Start the API server
python api_server.py

# Or with uvicorn
uvicorn api_server:app --reload

# API docs at http://localhost:8000/docs
```

#### API Endpoints:
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/start` | Start new test session |
| GET | `/api/question/{session_id}` | Get next question |
| POST | `/api/answer/{session_id}` | Submit answer |
| GET | `/api/progress/{session_id}` | Get progress |
| GET | `/api/results/{session_id}` | Get final results |
| GET | `/api/health` | Health check |

## 🧮 Adaptive Logic Explained

### Question Selection Algorithm

The adaptive engine uses a **multi-factor scoring approach**:

#### 1. Difficulty Targeting (50% weight)
```
estimated_ability = EMA(performance_signals)
target_difficulty = round(estimated_ability) + performance_adjustment

If recent_accuracy > 70%: adjustment = +1
If recent_accuracy < 40%: adjustment = -1
If consecutive_correct ≥ 2: additional +1
If consecutive_wrong ≥ 2: additional -1
```

#### 2. Category Diversity (30% weight)
- Every 3rd question targets the least-tested category
- Under-represented categories get selection bonus
- Weak categories are targeted for diagnostic depth

#### 3. Recency Adjustment (20% weight)
- Last 3 answers weighted more than overall history
- Streak detection for rapid difficulty changes
- Ability estimate uses EMA with α=0.3

#### Decision Flow:
```
User answers question
    → Update UserState (accuracy, ability, streaks)
    → Calculate target difficulty
    → Select target category
    → Get candidate questions
    → Score each candidate (difficulty match + diversity + diagnostics)
    → Select top candidate with controlled randomness
    → Generate explanation of why this question was chosen
    → Present question
```

### Why This Approach?

- **EMA for ability estimation**: Smoothly tracks ability changes while remaining responsive
- **Multi-factor scoring**: Balances difficulty matching with test coverage
- **Streak detection**: Enables rapid response to sustained patterns
- **Controlled randomness**: Top-3 weighted selection prevents predictability
- **Fallback broadening**: Progressive search relaxation ensures a question is always found

## 📁 Project Structure

```
adaptive-testing-system/
├── main.py                   # CLI entry point
├── app.py                    # Streamlit web UI
├── api_server.py            # FastAPI REST backend
├── config.py                # Configuration & constants
├── question_bank.py         # Question data & management
├── user_state.py            # User state tracking
├── adaptive_engine.py       # Core adaptive selection logic
├── scoring.py               # Score calculation
├── cognitive_profile.py     # Profile generation
├── llm_integration.py       # LLM/API integration
├── explanation_engine.py    # Decision explanations
├── test_runner.py           # Test orchestration
├── requirements.txt
├── .env.example
├── README.md
├── tests/
│   ├── test_adaptive_engine.py
│   ├── test_scoring.py
│   └── test_user_state.py
├── logs/
└── docs/
    ├── architecture.md
    └── adaptive_logic.md
```

## 🤖 AI Tool Usage Disclosure

### What was AI-assisted:
- **Question content**: Some question texts were generated with AI assistance, then manually reviewed, curated, and calibrated for difficulty
- **Prompt templates**: LLM prompt templates in `llm_integration.py` were iterated with AI assistance
- **Code review**: AI was used to review code for edge cases and potential improvements

### What was manually implemented:
- **Adaptive algorithm**: The multi-factor scoring, EMA-based ability estimation, and question selection logic
- **State management**: The UserState class with all tracking mechanisms
- **Scoring formulas**: Difficulty weighting, speed bonus, streak calculations
- **Architecture decisions**: Module structure, data flow, component responsibilities
- **Error handling**: Fallback mechanisms, API failure handling, input validation
- **Integration logic**: How components connect and interact
- **Test cases**: All test scenarios and assertions

### Error Handling:
- **LLM unavailable**: Full fallback to template-based profiles and built-in explanations
- **Invalid responses**: LLM output validated for relevance before use
- **API failures**: Graceful degradation with logging and user-friendly error messages
- **Edge cases**: Empty question bank, all questions asked, invalid inputs

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_adaptive_engine.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## 📊 Modularity & Extensibility

The system is designed to be easily extensible:

- **Add new question categories**: Add to `CognitiveCategory` enum and add questions
- **Add new question types**: Extend the `Question` dataclass
- **Change adaptive logic**: Modify weights in `Config` or override `AdaptiveEngine` methods
- **Add new agents**: The `TestRunner` orchestrator pattern supports adding new processing agents
- **Different LLM providers**: Swap `llm_integration.py` implementation
- **Database storage**: Replace in-memory state with database persistence
- **Different UIs**: Add any frontend — the `TestSession` API is UI-agnostic

## 📄 License

MIT License

## 👤 Author

Shreyash Sali — AI & Agentic Intelligence Internship Assessment"# adaptive-testing-system" 
