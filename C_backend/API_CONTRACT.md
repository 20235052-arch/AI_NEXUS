# Spleen Viewer — Backend API Contract (Dev C)

**Base URL (local dev):** `http://127.0.0.1:8000`

This document describes the endpoints Dev C's backend exposes, what
each one expects, and what it returns. All examples below are real
responses captured during testing on both CT and MR scans — not
hypothetical.

Interactive docs (try any endpoint live): `http://127.0.0.1:8000/docs`

---

## Overview / Flow

```
1. POST /upload            → get a study_id
2. GET  /slices/.../count  → get how many slices exist
3. GET  /slices/.../{i}    → get a 2D slice image (for the slider)
4. [Dev D writes mask.npy into storage/{study_id}/mask.npy]
5. GET  /metrics/{study_id} → get computed volume/metrics
```

Every endpoint after upload requires the `study_id` returned by
`POST /upload`. Nothing is accessible without it.

---

## `POST /upload`

Uploads a scan and parses it into an internal volume representation.

**Accepts** (multipart/form-data, field name `file`):
| Format | Notes |
|---|---|
| `.nii` / `.nii.gz` | Single NIfTI file |
| `.zip` | A zipped folder of a full DICOM series (**normal case for DICOM**) |
| `.dcm` | A single DICOM file (only valid if it's the entire series — rare) |

Both **CT** and **MR** DICOM series are supported and auto-detected.

**Returns** `200 OK`:
```json
{
  "study_id": "e23982bb-4c2b-4ed3-a7b2-b6d68d22861f",
  "shape": [5, 512, 512],
  "spacing": [4.0, 0.332, 0.332],
  "num_slices": 5,
  "modality": "CT"
}
```

| Field | Meaning |
|---|---|
| `study_id` | Unique ID — **pass this to every other endpoint** |
| `shape` | `[num_slices, height, width]` of the parsed volume |
| `spacing` | `[slice_thickness_mm, pixel_height_mm, pixel_width_mm]` |
| `num_slices` | Same as `shape[0]` — how many slices the slider should support |
| `modality` | `"CT"`, `"MR"`, or `"UNKNOWN"` (NIfTI files don't reliably store this) |

**Error responses:**
- `400` — unsupported file extension
- `422` — file couldn't be parsed (corrupt file, missing DICOM tags, unsupported compression codec, no `.dcm` files found in a zip, etc.) — `detail` field has the specific reason

---

## `GET /slices/{study_id}/count`

Returns how many slices the volume has, so the frontend slider can
set its range without loading every image first.

**Returns** `200 OK`:
```json
{ "num_slices": 5 }
```

**Error:** `404` if `study_id` doesn't exist.

---

## `GET /slices/{study_id}/{index}`

Returns a single 2D slice as a **PNG image** (`Content-Type: image/png`),
ready to display directly (e.g. `<img src="...">`).

`index` is 0-based, from `0` to `num_slices - 1`.

Windowing is automatic based on modality:
- **CT** → fixed soft-tissue Hounsfield-Unit windowing
- **MR / UNKNOWN** → adaptive percentile-based windowing (MR has no fixed intensity scale)

**Error responses:**
- `400` — index out of range (message states the valid range)
- `404` — study not found

---

## `GET /metrics/{study_id}`

Returns computed volume/metrics for the segmented spleen. **Requires
that a segmentation mask already exists** at
`storage/{study_id}/mask.npy` (produced by Dev D's pipeline — see
"Dependency on Dev D" below).

**Returns** `200 OK`:
```json
{
  "study_id": "e23982bb-4c2b-4ed3-a7b2-b6d68d22861f",
  "volume_cm3": 244.27,
  "voxel_count": 30000,
  "is_enlarged": false
}
```

| Field | Meaning |
|---|---|
| `volume_cm3` | Computed spleen volume in cubic centimeters |
| `voxel_count` | Raw number of voxels flagged as spleen in the mask |
| `is_enlarged` | `true` if `volume_cm3` exceeds ~314 cm³ (rough adult splenomegaly threshold — a simple flag, not a diagnosis) |

**Error responses:**
- `404` — study not found, **or** no `mask.npy` exists yet for this study (message distinguishes the two)

---

## Dependency on Dev D (AI & Meshing Backend)

The `/metrics` endpoint is the one part of this contract that depends
on another team member's output. It expects:

- **File path:** `storage/{study_id}/mask.npy`
- **Format:** a NumPy array, **same shape** as the original volume
  (`shape` from the `/upload` response)
- **Values:** `0` = not spleen, any value `> 0` = spleen

If Dev D's segmentation pipeline saves its output in this exact
format/location, `/metrics` will work with zero additional glue code.
**This is worth confirming directly with Dev D before final
integration.**

---

## Notes for other team members

- **Dev A (React frontend):** call `/upload` once per scan, then
  `/slices/.../count` to size the slider, then `/slices/.../{i}` on
  every slider move. Each slice call returns a raw PNG — no JSON
  wrapping needed for the image itself.
- **Dev B (3D/Three.js):** the 3D mesh comes from Dev D's pipeline,
  not from this backend. If clicking the 3D mesh needs to sync the
  2D slider to a matching slice index, that mapping (mesh Z-coordinate
  → slice index) needs to be defined jointly — flag this if it's
  needed for the demo.
- **Dev E (LLM & Trust Backend):** `/metrics` gives you real numbers
  (volume, enlargement flag) to ground generated explanations in
  actual data rather than the model inventing figures.
- **Member F:** all endpoints above have been tested against real CT
  and MR sample data, not just synthetic test files — see example
  responses above.

---

## Known limitations (as of this version)

- No authentication — fine for a hackathon/demo, not for production.
- Uploads are processed synchronously. If Dev D's real segmentation
  step is slow, consider adding an async job + status-poll pattern
  before final integration.
- `/metrics` assumes exactly one segmentation mask per study (no
  support for multiple organs/masks per study).
