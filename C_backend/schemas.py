"""
Request/response models for the LLM & Trust backend (Dev E).

Route shapes match Dev A's src/api.js EXACTLY as of the latest sync:
  GET  /anatomy/{structure}          (no /api prefix, no query params sent)
  POST /ask    { structure, question }
  POST /quiz   { structure, count }

Patient grounding: earlier versions of this file had a `PatientContext`
shaped like a full pipeline report (mesh_volume_mm3, confidence_score,
reference categories...). That data doesn't exist anywhere in the real
pipeline. Dev C's verified `/metrics/{study_id}` only returns
`volume_cm3`, `voxel_count`, `is_enlarged` -- so grounding now works by
passing an optional `study_id` and looking those three real fields up
server-side, not by the frontend constructing a patient_context blob.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


# ---------- GET /anatomy/{structure} ----------

class AnatomyResponse(BaseModel):
    structure: str
    display_name: str
    what_it_is: str
    function: str
    location: str
    neighboring_structures: list[str]
    anatomical_importance: str
    used_patient_data: bool
    disclaimer: str


# ---------- POST /ask ----------

class AskRequest(BaseModel):
    structure: str
    question: str
    session_id: Optional[str] = Field(
        None,
        description=(
            "Optional. Pass the same session_id across calls for the bot to "
            "remember earlier turns. Dev A's current askQuestion() call doesn't "
            "send this yet -- calls for the same structure share one loose "
            "default thread until it's added (see README)."
        ),
    )
    study_id: Optional[str] = Field(
        None,
        description=(
            "Optional. Dev C's study_id from /upload. If provided and that "
            "study has a real segmentation mask (Dev D's output), answers can "
            "cite this patient's actual volume_cm3 / is_enlarged via a tool "
            "call instead of general knowledge. Not currently sent by the "
            "frontend -- works fine without it."
        ),
    )


class AskResponse(BaseModel):
    structure: str
    question: str
    answer: str
    used_patient_data: bool
    disclaimer: str


# ---------- POST /quiz ----------

class QuizRequest(BaseModel):
    structure: str
    count: int = Field(3, ge=1, le=10)
    difficulty: Literal["intro", "intermediate", "advanced"] = "intro"  # optional; frontend doesn't send it yet


class QuizQuestion(BaseModel):
    id: str
    question: str
    options: list[str]
    correct_index: int
    explanation: str


class QuizResponse(BaseModel):
    structure: str
    questions: list[QuizQuestion]