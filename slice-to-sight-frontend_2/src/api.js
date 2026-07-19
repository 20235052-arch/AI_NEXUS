// src/api.js
//
// EVERY call to the backend goes through this file. Nowhere else in the app
// should you write `fetch(...)` directly.
//
// THIS FILE MATCHES DEV C'S REAL, VERIFIED CONTRACT (confirmed by running
// their actual code against a real test scan):
//   POST /upload                    -> { study_id, shape, spacing, num_slices, modality }
//   GET  /slices/{study_id}/count   -> { num_slices }
//   GET  /slices/{study_id}/{index} -> raw PNG image (not JSON)
//   GET  /metrics/{study_id}        -> { volume_cm3, voxel_count, is_enlarged }
//                                       (404 until Dev D writes mask.npy -- expected, not a bug)
//
// IMPORTANT DIFFERENCES FROM EARLIER VERSIONS OF THIS FILE:
//   - No /api prefix on any route.
//   - The ID field is `study_id`, not `job_id`. Renamed throughout the app.
//   - There is NO status/polling endpoint. Upload is synchronous -- it
//     parses the whole file and returns the final result in one response.
//     That means there is no separate "identifying" stage anymore; once
//     upload resolves, you already have everything you need.
//   - Metrics only returns volume_cm3, voxel_count, and is_enlarged --
//     NOT surface area, mean HU, or diameters. Those fields don't exist
//     in this backend. Don't display them as if they're real until
//     someone actually builds that.

export const BACKEND_URL = "http://localhost:8000"; // match Dev C's real uvicorn port

// --- PER-FEATURE SWITCHES ---
// false = hits the real backend now. true = still faked.
export const MOCK_FLAGS = {
  upload: false,        // Dev C — DONE, verified against real backend
  slices: false,        // Dev C — DONE, verified against real backend
  measurements: false,  // Dev C's endpoint is real and live, but 404s until
                         // Dev D writes storage/{study_id}/mask.npy -- handled
                         // gracefully below, not mocked.
  confidence: true,      // Dev D — not done yet
  mesh: true,             // Dev D — not done yet
  anatomy: true,           // Dev E — not done yet
  ask: true,                // Dev E — not done yet
  quiz: true,                 // Dev E — not done yet
};

const fakeDelay = (ms = 800) => new Promise((resolve) => setTimeout(resolve, ms));

// ---------- 1. UPLOAD ----------
//
// Synchronous: the response IS the finished result. No polling needed.

export async function uploadCT(file) {
  if (MOCK_FLAGS.upload) {
    await fakeDelay(1000);
    return {
      study_id: "study_demo123",
      shape: [40, 512, 512],
      spacing: [3.0, 0.7, 0.7],
      num_slices: 40,
      modality: "CT",
    };
  }

  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BACKEND_URL}/upload`, { method: "POST", body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Upload failed (${res.status})`);
  }
  return res.json();
}

// ---------- 2. SLICES (2D viewer) ----------
//
// Real backend splits this into two calls: get the count, then build
// direct image URLs for each index. Each slice URL returns a raw PNG,
// not JSON -- so we just construct URLs for <img src>, we don't fetch
// the image bytes ourselves.

export async function getSlices(studyId) {
  if (MOCK_FLAGS.slices) {
    await fakeDelay(500);
    const total = 40;
    return {
      study_id: studyId,
      total_slices: total,
      slices: Array.from({ length: total }, (_, i) => ({
        index: i,
        image_url: `https://placehold.co/512x512/0a1628/4ecdc4?text=Slice+${i}`,
      })),
    };
  }

  const res = await fetch(`${BACKEND_URL}/slices/${studyId}/count`);
  if (!res.ok) throw new Error(`Failed to fetch slice count (${res.status})`);
  const { num_slices } = await res.json();

  return {
    study_id: studyId,
    total_slices: num_slices,
    slices: Array.from({ length: num_slices }, (_, i) => ({
      index: i,
      image_url: `${BACKEND_URL}/slices/${studyId}/${i}`,
    })),
  };
}

// ---------- 3. METRICS (volume, voxel count, enlargement flag) ----------
//
// This endpoint is real and live, but depends on Dev D having written
// storage/{study_id}/mask.npy first. A 404 here is EXPECTED until Dev D's
// segmentation step runs -- it is not a bug, and the UI should say so
// honestly rather than showing fabricated numbers.
//
// NOTE: this backend does NOT provide surface_area_cm2, mean_hu, or
// diameters. If those are needed for the deck's measurements panel,
// that's a gap to flag with Dev C/D -- don't invent them here.

export async function getMeasurements(studyId) {
  if (MOCK_FLAGS.measurements) {
    await fakeDelay(600);
    return { status: "ready", volume_cm3: 162.7, voxel_count: 30000, is_enlarged: false };
  }

  const res = await fetch(`${BACKEND_URL}/metrics/${studyId}`);

  if (res.status === 404) {
    // Distinguish "mask not ready yet" from "study doesn't exist" using
    // the detail message the backend provides.
    const body = await res.json().catch(() => ({}));
    const pendingSegmentation = body.detail?.includes("segmentation mask");
    return {
      status: pendingSegmentation ? "pending_segmentation" : "not_found",
      detail: body.detail,
    };
  }

  if (!res.ok) throw new Error(`Failed to fetch metrics (${res.status})`);
  const data = await res.json();
  return { status: "ready", ...data };
}

// ---------- 4. AI TRUST PANEL (confidence) -- Dev D, not built yet ----------

export async function getConfidence(studyId, structure = "spleen") {
  if (MOCK_FLAGS.confidence) {
    await fakeDelay(500);
    return {
      study_id: studyId,
      structure,
      overall_confidence_pct: 92,
      low_confidence_regions: ["Superior Pole", "Splenic Hilum"],
      recommendation: "Manual review recommended in highlighted regions.",
    };
  }
  const res = await fetch(`${BACKEND_URL}/confidence/${studyId}/${structure}`);
  if (!res.ok) throw new Error(`Failed to fetch confidence (${res.status})`);
  return res.json();
}

// ---------- 5. MESH -- Dev D, not built yet ----------

export async function getMesh(studyId, structure = "spleen") {
  if (MOCK_FLAGS.mesh) {
    await fakeDelay(700);
    return { study_id: studyId, structure, mesh_url: null, format: "glb" };
  }
  const res = await fetch(`${BACKEND_URL}/mesh/${studyId}/${structure}`);
  if (!res.ok) throw new Error(`Failed to fetch mesh (${res.status})`);
  return res.json();
}

// ---------- 6. ANATOMY EXPLANATION -- Dev E, not built yet ----------

export async function getAnatomyInfo(structure = "spleen") {
  if (MOCK_FLAGS.anatomy) {
    await fakeDelay(600);
    return {
      structure,
      display_name: "Spleen",
      what_it_is: "A fist-sized, dark-red organ in the upper left abdomen, part of the lymphatic system.",
      function: "Filters blood, removes old red blood cells, and supports immune function.",
      location: "Left upper quadrant of the abdomen",
      neighboring_structures: ["Stomach", "Left Kidney", "Pancreatic Tail", "Diaphragm"],
      anatomical_importance: "Acts as a blood reservoir and immune surveillance site.",
    };
  }
  const res = await fetch(`${BACKEND_URL}/anatomy/${structure}`);
  if (!res.ok) throw new Error(`Failed to fetch anatomy info (${res.status})`);
  return res.json();
}

// ---------- 7. ASK A FREE-FORM QUESTION -- Dev E, not built yet ----------

export async function askQuestion(structure, question) {
  if (MOCK_FLAGS.ask) {
    await fakeDelay(900);
    return {
      structure,
      question,
      answer: "This is a mock answer. Once Dev E's /ask endpoint is live, this will be a real Claude-generated response.",
    };
  }
  const res = await fetch(`${BACKEND_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ structure, question }),
  });
  if (!res.ok) throw new Error(`Failed to get answer (${res.status})`);
  return res.json();
}

// ---------- 8. QUIZ MODE -- Dev E, not built yet ----------

export async function getQuiz(structure = "spleen", count = 3) {
  if (MOCK_FLAGS.quiz) {
    await fakeDelay(700);
    return {
      structure,
      questions: [
        {
          id: "q1",
          question: "Which organ lies immediately medial to the spleen's visceral surface?",
          options: ["Left kidney", "Stomach", "Pancreatic tail", "Left lung"],
          correct_index: 1,
          explanation: "The gastric impression on the spleen corresponds to the stomach.",
        },
      ].slice(0, count),
    };
  }
  const res = await fetch(`${BACKEND_URL}/quiz`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ structure, count }),
  });
  if (!res.ok) throw new Error(`Failed to fetch quiz (${res.status})`);
  return res.json();
}
