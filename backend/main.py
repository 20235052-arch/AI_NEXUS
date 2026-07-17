from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uuid

app = FastAPI()

# Crucial: This allows your React app (on port 5173) to talk to your API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    # Read the filename just to prove we got it
    print(f"Received file: {file.filename}")
    
    # Return a fake job_id back to the frontend
    return {"job_id": str(uuid.uuid4())}
