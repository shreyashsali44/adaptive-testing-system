"""
FastAPI Backend Server
Provides REST API for the adaptive testing system.

Author: [Candidate Name]
AI-Assisted: FastAPI route patterns referenced from documentation.
Business logic and integration are manual implementations.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid

from test_runner import TestSession
from config import Config

app = FastAPI(
    title="AI Adaptive Testing API",
    description="REST API for the AI-Powered Adaptive Cognitive Assessment System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (use Redis/DB in production)
sessions: dict[str, TestSession] = {}


class StartTestRequest(BaseModel):
    user_id: str = "user"
    num_questions: int = 10


class SubmitAnswerRequest(BaseModel):
    selected_answer: int
    confidence: Optional[str] = "medium"


class StartTestResponse(BaseModel):
    session_id: str
    message: str


@app.post("/api/start", response_model=StartTestResponse)
def start_test(request: StartTestRequest):
    """Start a new adaptive test session."""
    session_id = str(uuid.uuid4())[:8]
    num_q = max(5, min(request.num_questions, 20))
    sessions[session_id] = TestSession(user_id=request.user_id, max_questions=num_q)
    return StartTestResponse(
        session_id=session_id,
        message=f"Test session created with {num_q} questions."
    )


@app.get("/api/question/{session_id}")
def get_question(session_id: str):
    """Get the next question for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    question_data = session.get_next_question()

    if question_data is None:
        return {"test_complete": True, "message": "No more questions."}

    return {"test_complete": False, "question": question_data}


@app.post("/api/answer/{session_id}")
def submit_answer(session_id: str, request: SubmitAnswerRequest):
    """Submit an answer for the current question."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    result = session.submit_answer(
        selected_answer=request.selected_answer,
        confidence=request.confidence
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.get("/api/progress/{session_id}")
def get_progress(session_id: str):
    """Get current test progress."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return sessions[session_id].get_progress()


@app.get("/api/results/{session_id}")
def get_results(session_id: str):
    """Get final test results and cognitive profile."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return sessions[session_id].get_final_results()


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_sessions": len(sessions),
        "llm_available": bool(Config.OPENAI_API_KEY),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)