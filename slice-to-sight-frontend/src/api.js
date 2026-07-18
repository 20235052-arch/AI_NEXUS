// src/api.js
//
// EVERY call to the backend goes through this file. Nowhere else in the app
// should you write `fetch(...)` directly — that keeps all your backend
// contracts in one place, so when Dev C/D/E's real endpoints come online,
// you flip ONE switch (MOCK_MODE below) instead of hunting through components.

export const BACKEND_URL = "http://localhost:8000";

// --- THE ONE SWITCH ---
// true  = uses fake in-browser data, no backend needed at all (use this now)
// false = makes real fetch() calls to BACKEND_URL (flip this once Dev C/D/E are ready)
export const MOCK_MODE = true;

// Small helper so every mock function "feels" like a real network call
const fakeDelay = (ms = 800) => new Promise((resolve) => setTimeout(resolve, ms));

// ---------- 1. UPLOAD ----------

export async function uploadCT(file) {
  if (MOCK_MODE) {
    await fakeDelay(1000);
    return { job_id: "job_demo123", status: "processing", filename: file.name };
  }

  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BACKEND_URL}/api/upload`, { method: "POST", body: formData });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

// ---------- 2. STATUS (polling — tells us when identify/segment/mesh are done) ----------

export async function getStatus(jobId) {
  if (MOCK_MODE) {
    await fakeDelay(400);
    // Pretend it finishes after a couple of polls — see useJobPolling for how this is used
    return { job_id: jobId, status: "complete", organ_identified: "spleen" };
  }

  const res = await fetch(`${BACKEND_URL}/api/status/${jobId}`);
  if (!res.ok) throw new Error("Status check failed");
  return res.json();
}

// ---------- 3. SLICES (2D viewer) ----------

export async function getSlices(jobId) {
  if (MOCK_MODE) {
    await fakeDelay(500);
    const total = 40;
    return {
      job_id: jobId,
      orientation: "axial",
      total_slices: total,
      voxel_spacing_mm: { x: 1.0, y: 1.0, z: 1.0 },
      // Using a placeholder image service so the slider has something to show visually.
      slices: Array.from({ length: total }, (_, i) => ({
        index: i,
        image_url: `https://placehold.co/512x512/0a1628/4ecdc4?text=Slice+${i}`,
      })),
    };
  }

  const res = await fetch(`${BACKEND_URL}/api/slices/${jobId}`);
  if (!res.ok) throw new Error("Failed to fetch slices");
  return res.json();
}

// ---------- 4. SEGMENTATION METRICS (volume, surface area, etc.) ----------

export async function getMeasurements(jobId, structure = "spleen") {
  if (MOCK_MODE) {
    await fakeDelay(600);
    return {
      job_id: jobId,
      structure,
      measurements: {
        volume_cm3: 162.7,
        surface_area_cm2: 246.3,
        mean_hu: 48.6,
        max_diameter_cm: 12.4,
        min_diameter_cm: 7.1,
        thickness_cm: 6.3,
      },
      location: "Left upper quadrant of the abdomen",
      neighboring_structures: ["Stomach", "Left Kidney", "Pancreatic Tail", "Diaphragm"],
    };
  }

  const res = await fetch(`${BACKEND_URL}/api/segmentation/${jobId}/${structure}`);
  if (!res.ok) throw new Error("Failed to fetch measurements");
  return res.json();
}

// ---------- 5. AI TRUST PANEL (confidence) ----------

export async function getConfidence(jobId, structure = "spleen") {
  if (MOCK_MODE) {
    await fakeDelay(500);
    return {
      job_id: jobId,
      structure,
      overall_confidence_pct: 92,
      low_confidence_regions: ["Superior Pole", "Splenic Hilum"],
      recommendation: "Manual review recommended in highlighted regions.",
    };
  }

  const res = await fetch(`${BACKEND_URL}/api/confidence/${jobId}/${structure}`);
  if (!res.ok) throw new Error("Failed to fetch confidence");
  return res.json();
}

// ---------- 6. MESH URL (for Dev B's 3D viewer) ----------

export async function getMesh(jobId, structure = "spleen") {
  if (MOCK_MODE) {
    await fakeDelay(700);
    return { job_id: jobId, structure, mesh_url: null, format: "glb" }; // Dev B plugs the real .glb in later
  }

  const res = await fetch(`${BACKEND_URL}/api/mesh/${jobId}/${structure}`);
  if (!res.ok) throw new Error("Failed to fetch mesh");
  return res.json();
}

// ---------- 7. ANATOMY EXPLANATION (click-to-learn) ----------

export async function getAnatomyInfo(structure = "spleen") {
  if (MOCK_MODE) {
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

  const res = await fetch(`${BACKEND_URL}/api/anatomy/${structure}`);
  if (!res.ok) throw new Error("Failed to fetch anatomy info");
  return res.json();
}

// ---------- 8. ASK A FREE-FORM QUESTION (Step 5: interact) ----------

export async function askQuestion(structure, question) {
  if (MOCK_MODE) {
    await fakeDelay(900);
    return {
      structure,
      question,
      answer:
        "This is a mock answer. Once Dev E's /api/ask endpoint is live, this will be a real Claude-generated response grounded in the clicked structure.",
    };
  }

  const res = await fetch(`${BACKEND_URL}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ structure, question }),
  });
  if (!res.ok) throw new Error("Failed to get answer");
  return res.json();
}

// ---------- 9. QUIZ MODE ----------

export async function getQuiz(structure = "spleen", count = 3) {
  if (MOCK_MODE) {
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
        {
          id: "q2",
          question: "What is the primary function of the spleen?",
          options: ["Hormone production", "Filtering blood & immune support", "Digestion", "Bile storage"],
          correct_index: 1,
          explanation: "The spleen filters blood and removes old red blood cells.",
        },
        {
          id: "q3",
          question: "In which abdominal quadrant is the spleen located?",
          options: ["Right upper", "Left upper", "Right lower", "Left lower"],
          correct_index: 1,
          explanation: "The spleen sits in the left upper quadrant, protected by the ribcage.",
        },
      ].slice(0, count),
    };
  }

  const res = await fetch(`${BACKEND_URL}/api/quiz`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ structure, count }),
  });
  if (!res.ok) throw new Error("Failed to fetch quiz");
  return res.json();
}
