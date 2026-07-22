
from fastapi import APIRouter, HTTPException

from schemas import (
    AnatomyResponse,
    AskRequest, AskResponse,
    QuizRequest, QuizResponse,
)
import llm_service as llm_service

router = APIRouter()


@router.get("/anatomy/{structure}", response_model=AnatomyResponse)
def get_anatomy(structure: str, study_id: str | None = None):
    try:
        result = llm_service.explain_structure(structure, study_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq API error: {e}")
    return AnatomyResponse(**result)


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    try:
        answer, used_patient_data = llm_service.ask_question(
            req.structure, req.question, req.session_id, req.study_id,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq API error: {e}")

    return AskResponse(
        structure=req.structure,
        question=req.question,
        answer=answer,
        used_patient_data=used_patient_data,
        disclaimer=llm_service.DISCLAIMER,
    )


@router.delete("/ask/{session_id}")
def clear_ask_session(session_id: str):
    import session_store
    session_store.clear(session_id)
    return {"cleared": session_id}


@router.post("/quiz", response_model=QuizResponse)
def quiz(req: QuizRequest):
    try:
        result = llm_service.generate_quiz(req.structure, req.count, req.difficulty)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq API error: {e}")
    return QuizResponse(**result)