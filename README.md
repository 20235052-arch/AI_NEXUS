for dev d
```bash
pip install -r requirements.txt
```

in a .env file:
(rename the .env.example file to .env and add your groq api key)
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

```bash
uvicorn standalone_main:app --reload --port 8010
```

Open `http://127.0.0.1:8010/docs` and try, in this order:

- **`GET /anatomy/Spleen`** — no `study_id`. Confirm you get back
  `what_it_is`, `function`, `location`, `neighboring_structures`,
  `anatomical_importance`, and `used_patient_data: false`.
- **`POST /ask`** with `{"structure": "Spleen", "question": "What does it do?"}`
  — confirm `used_patient_data: false` and a sensible `answer`.
- **`POST /ask`** again with a follow-up question — same `structure`, no
  `session_id` — confirm the answer reads like a natural follow-up (loose
  per-structure memory is working).
- **`POST /quiz`** with `{"structure": "Spleen", "count": 3}` — confirm 3
  questions come back with `id`, `options`, `correct_index`, `explanation`.
- **Ask it to diagnose something** — e.g. `"does this spleen look diseased?"`
  — confirm it declines and redirects to a clinician rather than
  speculating. 

