"""
Codespace Cortex - Assessment Agent (Phase 2, Step 1)

Run with:
    uvicorn app.main:app --reload

Then test with:
    curl -X POST http://localhost:8000/assessment/grade -H "Content-Type: application/json" -d @sample_request.json
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from app.db import (
    init_db, save_grade, get_grades_for_student,
    add_course_content, log_conversation,
)
from app.assessment import grade_submission
from app.tutor import ask_tutor

load_dotenv()

app = FastAPI(title="Codespace Cortex - Assessment Agent")


@app.on_event("startup")
def startup():
    init_db()


# ---- Request/response models ----

class RubricCriterion(BaseModel):
    criterion: str
    max_points: float
    description: str


class GradeRequest(BaseModel):
    tenant_id: str
    student_id: str
    assignment_id: str
    submission_text: str
    rubric: list[RubricCriterion]


class CourseContentRequest(BaseModel):
    tenant_id: str
    course_id: str
    title: str
    chunk_text: str


class TutorAskRequest(BaseModel):
    tenant_id: str
    student_id: str
    course_id: str
    question: str
    mode: str = "free_help"  # "free_help" or "graded_work"


# ---- Routes ----

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/assessment/grade")
def grade(req: GradeRequest):
    rubric_dicts = [r.model_dump() for r in req.rubric]

    try:
        result = grade_submission(req.submission_text, rubric_dicts)
    except ValueError as e:
        # Model returned unparseable output - don't silently save garbage.
        raise HTTPException(status_code=502, detail=str(e))

    save_grade(
        tenant_id=req.tenant_id,
        student_id=req.student_id,
        assignment_id=req.assignment_id,
        submission_text=req.submission_text,
        rubric=rubric_dicts,
        result=result,
    )

    return result


@app.get("/assessment/grades/{tenant_id}/{student_id}")
def list_grades(tenant_id: str, student_id: str):
    return get_grades_for_student(tenant_id, student_id)


# ---- Phase 1: Tutor agent + content ingestion ----

@app.post("/content/ingest")
def ingest_content(req: CourseContentRequest):
    """
    Loads a chunk of course material for retrieval. In a real system this
    would be triggered by the connector layer syncing from the LMS; for
    now, call this directly to seed course content for testing the tutor.
    """
    add_course_content(req.tenant_id, req.course_id, req.title, req.chunk_text)
    return {"status": "ingested"}


@app.post("/tutor/ask")
def tutor_ask(req: TutorAskRequest):
    if req.mode not in ("free_help", "graded_work"):
        raise HTTPException(status_code=400, detail="mode must be 'free_help' or 'graded_work'")

    try:
        answer = ask_tutor(req.tenant_id, req.student_id, req.course_id, req.question, req.mode)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    log_conversation(req.tenant_id, req.student_id, req.course_id, req.question, answer, req.mode)

    return {"answer": answer, "mode": req.mode}
