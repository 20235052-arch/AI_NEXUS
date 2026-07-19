# Spleen Viewer Backend (Dev C)

Handles file uploads, slices DICOM/NIfTI scans into 2D images, and
calculates volume/metrics from a segmentation mask.

## Setup

You already have a `venv` folder from before. If this is a fresh copy,
create one first:

```powershell
python -m venv venv
```

Activate it:

```powershell
venv\Scripts\Activate.ps1
```

If PowerShell blocks the script, run this once (no admin needed):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run the server

```powershell
uvicorn main:app --reload
```

Then open your browser to:

- http://127.0.0.1:8000/ → health check
- http://127.0.0.1:8000/docs → interactive API docs (Swagger UI) —
  you can upload a test file and try every endpoint right from here,
  no frontend needed yet.

## Endpoints

### `POST /upload`
Upload a `.nii`, `.nii.gz`, `.dcm`, or `.zip` (a zipped folder of a
full DICOM series) file. Returns a `study_id` that every other
endpoint needs.

```json
{
  "study_id": "b3f1...",
  "shape": [120, 512, 512],
  "spacing": [1.5, 0.7, 0.7],
  "num_slices": 120,
  "modality": "CT"
}
```

Both CT and MR DICOM series are supported. CT scans get converted to
Hounsfield Units (the standard CT intensity scale); MR scans don't
have a standardized scale, so slices are windowed adaptively instead
(see `/slices` below).

### `GET /slices/{study_id}/count`
Returns how many slices the volume has (for the frontend slider range).

### `GET /slices/{study_id}/{index}`
Returns a single 2D slice as a PNG image. CT scans use fixed
soft-tissue windowing; MR (or unrecognized modality) scans use
adaptive percentile-based windowing instead, since MR has no fixed
intensity scale.

### `GET /metrics/{study_id}`
Returns computed volume/metrics. Requires that a `mask.npy` file
(same shape as the volume, from Dev D's segmentation step) has
already been placed in `storage/{study_id}/mask.npy`.

```json
{
  "study_id": "b3f1...",
  "volume_cm3": 245.3,
  "voxel_count": 163533,
  "is_enlarged": false
}
```

## Testing without a real segmentation model yet

Until Dev D's pipeline is ready, you can fake a mask to test the
`/metrics` endpoint. After uploading a scan (note the `study_id` it
returns), run this in a Python shell from the project folder:

```python
import numpy as np

study_id = "PASTE_YOUR_STUDY_ID_HERE"
volume = np.load(f"storage/{study_id}/volume.npy")

# Fake mask: just mark a random blob as "spleen" so you can test the
# metrics math end-to-end.
fake_mask = np.zeros_like(volume, dtype=np.uint8)
fake_mask[40:60, 200:260, 150:210] = 1

np.save(f"storage/{study_id}/mask.npy", fake_mask)
```

Then hit `GET /metrics/{study_id}` and confirm you get sensible numbers
back.

## Project structure

```
spleen-backend/
  main.py                 # FastAPI app, wires routers together
  requirements.txt
  routers/
    upload.py              # POST /upload
    slices.py               # GET /slices/...
    metrics.py               # GET /metrics/...
  services/
    volume_loader.py         # DICOM/NIfTI -> numpy volume
  storage/                    # uploaded scans + cached volumes live here
```

## Next steps / API contract with the team

- **Dev D (AI & Meshing)**: needs to read `storage/{study_id}/volume.npy`,
  run segmentation, and save the result to
  `storage/{study_id}/mask.npy` (same shape as the volume, values >0
  = spleen).
- **Dev A (React frontend)**: calls `/upload`, then `/slices/{study_id}/count`
  to size the slider, then `/slices/{study_id}/{index}` on every
  slider move.
- **Dev B (3D/Three.js)**: will get the actual 3D mesh file from Dev D
  (not from this backend) — but may want slice index <-> Z-coordinate
  mapping from here to sync 2D/3D views. Flag this to the team if so.
- **Dev E (LLM backend)**: will likely call `/metrics/{study_id}` to
  get real numbers to reference in generated explanations.
