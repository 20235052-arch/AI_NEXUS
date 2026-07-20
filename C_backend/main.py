"""
Entry point for the Spleen Viewer backend (Dev C's service).

Run with:
    uvicorn main:app --reload

Then visit http://127.0.0.1:8000/docs for interactive API docs.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  #Without StaticFiles --> 404 Not Found

from routers import (
    upload,
    slices,
    metrics,
    segmentation,
    mesh,
)
app = FastAPI(title="Spleen Viewer Backend")

# Allow the React frontend (running on a different port, e.g. 3000/5173)
# to call this API during development. Tighten allow_origins before
# deploying anywhere public.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(slices.router)
app.include_router(metrics.router)
app.include_router(segmentation.router)
app.include_router(mesh.router)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "spleen-backend"}

app.mount(      #FastAPI has no idea that the storage folder should be accessible over the web.
    "/storage",
    StaticFiles(directory="storage"),
    name="storage",
)
