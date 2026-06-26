import os
import shutil
import uuid
from dotenv import load_dotenv

# Load .env BEFORE importing app modules so GROQ_API_KEY is set when ChatGroq initialises
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.text_engine import extract_text_from_pdf, chunk_text_uniform, chunk_text_for_rag
from app.services.vector_store import get_vector_store
from app.graphs.auto_graph import auto_mode_graph
from app.graphs.pilot_graph import pilot_mode_graph

app = FastAPI(title="Vizzy Core Backend")

# --- CORS ---
# In production set ALLOWED_ORIGINS env var to your actual frontend domain,
# e.g. "https://vizzy.example.com". Defaults to localhost for dev.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.abspath("./data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 20 MB upload limit
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".txt"}
ALLOWED_CONTENT_TYPES = {"application/pdf", "text/plain"}


class PilotQueryRequest(BaseModel):
    user_query: str
    collection_name: str


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    # Extension check
    _, ext = os.path.splitext(file.filename or "")
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and TXT are supported.")

    # Read into memory first so we can enforce size limit
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_UPLOAD_BYTES // (1024*1024)} MB.")

    # Sanitise filename — strip path components, use only the basename
    safe_name = os.path.basename(file.filename).replace("..", "").replace("/", "").replace("\\", "")
    if not safe_name:
        safe_name = f"{uuid.uuid4().hex}{ext}"

    file_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    collection_name = os.path.splitext(safe_name)[0]
    collection_name = "".join(e for e in collection_name if e.isalnum()).lower()
    if not collection_name:
        collection_name = uuid.uuid4().hex

    if ext.lower() == ".pdf":
        text = extract_text_from_pdf(file_path)
    else:
        text = contents.decode("utf-8", errors="replace")

    chunks = chunk_text_for_rag(text)
    vector_store = get_vector_store(collection_name=collection_name)
    vector_store.add_texts(chunks)

    return {
        "filename": safe_name,
        "collection_name": collection_name,
        "total_chunks": len(chunks),
        "filePath": file_path,
    }


@app.post("/api/auto-mode")
async def run_auto_mode(file_path: str = Form(...), total_frames: int = Form(...)):
    # Prevent path traversal: resolve and confirm it's inside UPLOAD_DIR
    resolved = os.path.realpath(os.path.abspath(file_path))
    if not resolved.startswith(UPLOAD_DIR):
        raise HTTPException(status_code=400, detail="Invalid file path.")

    if not os.path.exists(resolved):
        raise HTTPException(status_code=404, detail="Target text source file not found.")

    # Clamp frames to a safe range
    total_frames = max(1, min(total_frames, 20))

    if resolved.endswith(".pdf"):
        text = extract_text_from_pdf(resolved)
    else:
        with open(resolved, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

    segments = chunk_text_uniform(text, total_frames)
    initial_state = {
        "text_segments": segments,
        "current_index": 0,
        "total_frames": total_frames,
        "collection": [],
    }
    result = auto_mode_graph.invoke(initial_state)
    return {"collection": result["collection"]}


@app.post("/api/pilot-mode")
async def run_pilot_mode(payload: PilotQueryRequest):
    # Basic input length guard
    if len(payload.user_query.strip()) == 0:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    if len(payload.user_query) > 2000:
        raise HTTPException(status_code=400, detail="Query too long. Max 2000 characters.")

    initial_state = {
        "user_query": payload.user_query,
        "collection_name": payload.collection_name,
        "chat_reply": "",
        "generated_image_url": "",
    }
    result = pilot_mode_graph.invoke(initial_state)
    return {"reply": result["chat_reply"], "imageUrl": result["generated_image_url"]}
