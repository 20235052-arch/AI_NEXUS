"""
LLM & Trust backend — Groq API integration (free tier, Llama 3.3 70B by default).

Design principles (this is the "Trust Backend" contract):
1. The model explains anatomy; it never diagnoses disease. Enforced in every
   system prompt below, not just mentioned once.
2. Patient-specific numbers are NEVER left to the model to recall or
   estimate. They come from Dev C's real, verified /metrics/{study_id}
   endpoint (volume_cm3, voxel_count, is_enlarged) via the
   get_patient_measurement tool, so a number the UI shows always traces
   back to actual pipeline output, not the model's imagination.
3. /anatomy and /quiz try to force structured tool-call output. Open-weight
   models are less reliable at this than a frontier model — if the model
   talks instead of calling the tool, we fall back to packaging its text
   into the expected shape rather than crashing the endpoint.

Groq's API is OpenAI-compatible: tool schemas use {"type": "function",
"function": {...}}, tool results go back as {"role": "tool", ...} messages,
and tool_choice can be "auto", "required", or a specific function name.
"""

import os
import json
import time
from pathlib import Path

import numpy as np
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
_client = Groq(api_key=os.environ["GROQ_API_KEY"])

STORAGE = Path("storage")  # same folder Dev C's routers use, relative to wherever uvicorn runs
SPLENOMEGALY_THRESHOLD_CM3 = 314  # matches Dev C's routers/metrics.py — kept in sync, not re-derived


def _create_with_retry(max_attempts: int = 3, **kwargs):
    """Wraps _client.chat.completions.create with retries.

    Open-weight models on Groq occasionally emit a malformed tool call as
    literal text (e.g. mixing a refusal sentence with an attempted
    <function=...> call) instead of a proper structured tool_calls response.
    Groq's server rejects that with a 400 'tool_use_failed' error. This is
    inherently probabilistic — the same prompt usually succeeds on a retry —
    so we retry a couple of times before giving up, rather than failing the
    whole request on the first bad generation.
    """
    last_error = None
    for attempt in range(max_attempts):
        try:
            return _client.chat.completions.create(**kwargs)
        except Exception as e:
            last_error = e
            if attempt < max_attempts - 1:
                time.sleep(0.5 * (attempt + 1))  # brief backoff before retrying
    raise last_error

DISCLAIMER = (
    "Educational information only. This explains anatomy — it does not "
    "diagnose disease or replace a qualified clinician."
)

BASE_SYSTEM_PROMPT = """You are the anatomy-explanation assistant inside an \
"Anatomical Intelligence" platform. Students and clinicians explore a \
patient's segmented CT scan and 3D anatomical reconstruction, and ask you \
to explain what they're looking at.

Hard rules, no exceptions:
- You explain anatomy: what a structure is, what it does, what's near it, \
why it matters. You NEVER diagnose disease, NEVER speculate about whether \
a finding is pathological, and NEVER suggest a treatment or next clinical \
step. If asked to diagnose or interpret a finding clinically, say plainly \
that you explain anatomy and can't diagnose, and suggest the person bring \
the finding to a qualified clinician — but don't stop there. Follow that \
with real educational content: e.g. what "enlarged" means for this \
structure, roughly what range counts as typical, and general reasons an \
organ can be flagged as enlarged. The line you don't cross is telling THIS \
patient what THEIR finding means clinically — it is not "refuse to discuss \
the topic at all." A one-sentence deflection with no actual information is \
not a good answer; a substantive, educational answer that stops short of a \
clinical judgment about this patient is.
- If patient-specific data is available to you via the get_patient_measurement \
tool, use it and be explicit that a number is this patient's measured value \
("this patient's segmented spleen measures...") rather than a general \
textbook figure. Never invent a patient-specific number — call the tool.
- Looking up a measurement (volume, whether it's flagged as enlarged, etc.) \
is NOT diagnosing — it's just reporting a number your pipeline already \
computed. Call get_patient_measurement freely for these; you only need to \
decline when asked to interpret a finding clinically (what it means, \
whether it's concerning, what to do about it) rather than to report the \
measurement itself.
- The get_patient_measurement tool may return "not available" — if so, say \
so and answer with general anatomical knowledge instead. Do not treat \
"not available" as zero or as evidence of anything.
- Keep the tone clear and educational, appropriate for a motivated student \
or a clinician doing a quick refresher — not oversimplified, not needlessly \
jargon-heavy.
- When asked to produce a structured result (an explanation or quiz \
questions), you MUST respond by calling the matching tool/function — do not \
answer in plain text for those requests.
"""


# ---------------------------------------------------------------------------
# Real patient data lookup — reads the SAME storage Dev C's /metrics endpoint
# reads, so numbers are guaranteed consistent with what the Measurements
# panel shows. No network round-trip needed since this runs in the same
# process once mounted into the shared app (see routers/anatomy.py).
# ---------------------------------------------------------------------------

def _load_real_metrics(study_id: str) -> dict | None:
    """Returns {volume_cm3, voxel_count, is_enlarged} for a study, or None
    if the study or its segmentation mask doesn't exist yet. Mirrors the
    exact logic in Dev C's routers/metrics.py — kept deliberately duplicated
    rather than imported, so this module works whether or not it's mounted
    inside Dev C's app (e.g. during solo testing via standalone_main.py)."""
    if not study_id:
        return None

    study_dir = STORAGE / study_id
    mask_path = study_dir / "mask.npy"
    spacing_path = study_dir / "spacing.npy"

    if not mask_path.exists() or not spacing_path.exists():
        return None

    try:
        mask = np.load(mask_path)
        spacing = np.load(spacing_path)
    except Exception:
        return None

    voxel_volume_mm3 = float(spacing[0] * spacing[1] * spacing[2])
    voxel_count = int(np.sum(mask > 0))
    volume_cm3 = round((voxel_count * voxel_volume_mm3) / 1000, 2)

    return {
        "volume_cm3": volume_cm3,
        "voxel_count": voxel_count,
        "is_enlarged": volume_cm3 > SPLENOMEGALY_THRESHOLD_CM3,
    }


PATIENT_DATA_TOOL = {
    "type": "function",
    "function": {
        "name": "get_patient_measurement",
        "description": (
            "Look up a real measured value for the current patient's segmented "
            "spleen, computed from Dev C's backend. Always call this instead of "
            "recalling or estimating a patient-specific number yourself. "
            "Returns 'not available' if no study_id was given or no segmentation "
            "mask exists yet for that study."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "field": {
                    "type": "string",
                    "enum": ["volume_cm3", "voxel_count", "is_enlarged"],
                    "description": "Which measurement to retrieve.",
                }
            },
            "required": ["field"],
        },
    },
}


def _lookup_patient_field(field: str, metrics: dict | None) -> str:
    if metrics is None:
        return "not available (no study_id was provided, or no segmentation mask exists yet for this study)"
    value = metrics.get(field)
    if value is None:
        return f"not available (field '{field}' unexpected)"
    return json.dumps(value)


def _to_message_dict(message) -> dict:
    """Converts a Groq/OpenAI-style response message object into the plain
    dict shape needed to feed it back into the next request's `messages`."""
    msg = {"role": "assistant", "content": message.content}
    if message.tool_calls:
        msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in message.tool_calls
        ]
    return msg


def _run_tool_loop(messages: list[dict], system: str, metrics: dict | None,
                    tools: list[dict], tool_choice="auto", max_rounds: int = 4):
    used_patient_data = False
    full_messages = [{"role": "system", "content": system}] + messages

    for _ in range(max_rounds):
        response = _create_with_retry(
            model=MODEL,
            messages=full_messages,
            tools=tools,
            tool_choice=tool_choice,
            max_tokens=1024,
        )
        message = response.choices[0].message

        if not message.tool_calls:
            return message, used_patient_data, full_messages

        # If the model called anything OTHER than the lookup tool, that's a
        # final structured answer (e.g. structure_explanation, quiz_questions)
        # -- return it immediately. There's no "tool" result to send back for
        # it, so looping further would leave that tool_call unanswered and
        # the next API call would be rejected as an invalid conversation.
        non_lookup_calls = [tc for tc in message.tool_calls if tc.function.name != "get_patient_measurement"]
        if non_lookup_calls:
            return message, used_patient_data, full_messages

        full_messages.append(_to_message_dict(message))
        for tc in message.tool_calls:
            used_patient_data = metrics is not None
            args = json.loads(tc.function.arguments)
            result_text = _lookup_patient_field(args.get("field", ""), metrics)
            full_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_text,
            })

        if isinstance(tool_choice, dict):
            tool_choice = "required"

    return message, used_patient_data, full_messages


def _extract_tool_call(message, tool_name: str):
    if not message.tool_calls:
        return None
    for tc in message.tool_calls:
        if tc.function.name == tool_name:
            try:
                return json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                return None
    return None


# ---------------------------------------------------------------------------
# /anatomy/{structure}
# ---------------------------------------------------------------------------

EXPLAIN_TOOL = {
    "type": "function",
    "function": {
        "name": "structure_explanation",
        "description": "Return a structured anatomical explanation of a clicked structure.",
        "parameters": {
            "type": "object",
            "properties": {
                "what_it_is": {"type": "string"},
                "function": {"type": "string"},
                "location": {
                    "type": "string",
                    "description": "General anatomical location, e.g. 'Left upper quadrant of the abdomen'.",
                },
                "neighboring_structures": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3-6 short items naming structures adjacent to this one.",
                },
                "anatomical_importance": {"type": "string"},
            },
            "required": ["what_it_is", "function", "location", "neighboring_structures", "anatomical_importance"],
        },
    },
}


def explain_structure(structure: str, study_id: str | None = None) -> dict:
    metrics = _load_real_metrics(study_id) if study_id else None
    tools = [PATIENT_DATA_TOOL, EXPLAIN_TOOL]
    messages = [{
        "role": "user",
        "content": (
            f"Explain the anatomical structure: {structure}. "
            f"If patient-specific measurements are available and relevant "
            f"(e.g. whether this patient's is flagged as enlarged), weave them "
            f"in via the tool. Call structure_explanation with your final answer."
        ),
    }]

    message, used_patient_data, _ = _run_tool_loop(
        messages, BASE_SYSTEM_PROMPT, metrics, tools,
        tool_choice={"type": "function", "function": {"name": "structure_explanation"}},
    )

    parsed = _extract_tool_call(message, "structure_explanation")
    if parsed is None:
        fallback_text = message.content or "The model did not return a structured explanation."
        parsed = {
            "what_it_is": fallback_text,
            "function": "(not returned in structured form — see what_it_is)",
            "location": "(not returned in structured form)",
            "neighboring_structures": [],
            "anatomical_importance": "(not returned in structured form)",
        }

    return {
        "structure": structure,
        "display_name": structure.strip().title(),
        "used_patient_data": used_patient_data,
        "disclaimer": DISCLAIMER,
        **parsed,
    }


# ---------------------------------------------------------------------------
# /ask
# ---------------------------------------------------------------------------

def ask_question(structure: str, question: str, session_id: str | None,
                  study_id: str | None):
    import session_store  # imported here to avoid a hard dependency for anyone unit-testing pure LLM logic

    metrics = _load_real_metrics(study_id) if study_id else None
    session_key = session_id or f"anon:{structure.strip().lower()}"
    history = session_store.get_history(session_key)

    user_message = f"Structure in focus: {structure}. Question: {question}"
    messages = history + [{"role": "user", "content": user_message}]

    message, used_patient_data, full_messages = _run_tool_loop(
        messages, BASE_SYSTEM_PROMPT, metrics,
        tools=[PATIENT_DATA_TOOL], tool_choice="auto",
    )
    answer = (message.content or "").strip()
    if not answer:
        answer = "Sorry, I wasn't able to generate a response that time — try asking again."

    persisted = [m for m in full_messages if m["role"] != "system"]
    persisted.append({"role": "assistant", "content": answer})
    session_store.get_history(session_key).clear()
    session_store.append_and_trim(session_key, persisted)

    return answer, used_patient_data


# ---------------------------------------------------------------------------
# /quiz
# ---------------------------------------------------------------------------

QUIZ_TOOL = {
    "type": "function",
    "function": {
        "name": "quiz_questions",
        "description": "Return a set of multiple-choice anatomy quiz questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "options": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 3,
                                "maxItems": 5,
                            },
                            "correct_index": {"type": "integer"},
                            "explanation": {
                                "type": "string",
                                "description": "Why the correct answer is correct — shown after the student answers.",
                            },
                        },
                        "required": ["question", "options", "correct_index", "explanation"],
                    },
                }
            },
            "required": ["questions"],
        },
    },
}


def generate_quiz(structure: str, count: int, difficulty: str) -> dict:
    system = BASE_SYSTEM_PROMPT + (
        "\nYou are writing anatomy quiz questions, not clinical/board-exam "
        "diagnostic questions. Test knowledge of structure, function, and "
        "relationships to nearby anatomy — never disease diagnosis or "
        "clinical decision-making."
    )
    messages = [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                f"Write {count} multiple-choice quiz question(s) about the "
                f"{structure}, difficulty level: {difficulty}. Call quiz_questions "
                f"with the result."
            ),
        },
    ]

    response = _create_with_retry(
        model=MODEL,
        messages=messages,
        tools=[QUIZ_TOOL],
        tool_choice={"type": "function", "function": {"name": "quiz_questions"}},
        max_tokens=2048,
    )
    message = response.choices[0].message
    parsed = _extract_tool_call(message, "quiz_questions")
    if parsed is None:
        raise RuntimeError(
            "Model did not return quiz_questions in structured form. "
            "Raw response: " + (message.content or "(empty)")
        )

    questions = [{"id": f"q{i+1}", **q} for i, q in enumerate(parsed["questions"])]
    return {"structure": structure, "questions": questions}