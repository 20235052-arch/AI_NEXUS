# Segmentation Probability Output — Format Agreement

**Between:** Member 3 (Segmentation/Probabilities) and Member 4 (consumes this in metrics/trust panel)

This replaces the old hard yes/no `mask.npy` with a per-voxel
confidence value, so downstream code can show an overall trust score
and flag specific low-confidence regions instead of a single silent
binary decision.

## Files produced by Member 3, per study

### 1. `storage/{study_id}/spleen_probability.npy`

| Property | Value |
|---|---|
| Type | NumPy array (`.npy`) |
| Shape | Identical to `storage/{study_id}/volume.npy` — `(num_slices, height, width)` |
| Dtype | `float32` |
| Value range | `0.0` – `1.0` (probability this voxel is spleen) |

### 2. `storage/{study_id}/confidence_summary.json`

```json
{
  "overall_score": 0.91,
  "overall_score_percent": 91,
  "threshold_used": 0.5,
  "predicted_voxel_count": 30412,
  "low_confidence_voxel_count": 812
}
```

| Field | Meaning |
|---|---|
| `overall_score` | Mean probability across all voxels predicted as spleen (i.e. probability > threshold), as a raw 0-1 value |
| `overall_score_percent` | Same value, rounded to a whole-number percentage — **this is what the UI should display to the user** (e.g. "91% confident"), so the frontend doesn't need to do the conversion itself |
| `threshold_used` | The probability cutoff used to decide "is this voxel spleen" (`0.5`) |
| `predicted_voxel_count` | Number of voxels above the threshold |
| `low_confidence_voxel_count` | Of those, how many are below `0.7` — i.e. "predicted as spleen but not confidently" |

## How Member 4 derives a binary mask from this (if still needed)

```python
import numpy as np

probs = np.load(f"storage/{study_id}/spleen_probability.npy")
mask = probs > 0.5   # same threshold as confidence_summary.json
voxel_count = np.sum(mask)
```

This keeps existing volume/voxel-count calculations working exactly
as before — `mask` behaves identically to the old `mask.npy`, it's
just derived on the consuming side instead of pre-thresholded by
Member 3.

## Integration check (do this before wiring into the real pipeline)

1. Member 3 runs `make_sample_output.py` to generate a real,
   correctly-formatted sample (no TotalSegmentator install required
   for this step).
2. Member 4 loads `spleen_probability.npy` and `confidence_summary.json`
   directly — using only the code shown above — and confirms it works
   with **zero additional questions or code changes**.
3. Once confirmed, Member 3 wires in the real `run_segmentation.py`
   (which does require TotalSegmentator installed) to replace the
   sample generator for real scans.

## Decisions (resolved)

- **Threshold:** keeping `0.5` — no change.
- **Display format:** the UI shows `overall_score_percent` (a whole
  number, e.g. `91`), not the raw `0.0`-`1.0` score. The JSON now
  includes both, so no conversion is needed on the consuming side.
- **Low-confidence regions (grouped, with coordinates):** left out of
  scope for now. `low_confidence_voxel_count` (a simple count) is
  enough for the MVP. Can revisit if there's time later.
