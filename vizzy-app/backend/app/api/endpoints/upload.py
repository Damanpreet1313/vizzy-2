from fastapi import APIRouter, UploadFile, File, HTTPException
import os, shutil
from pathlib import Path
from app.services.text_engine import extract_text_from_pdf, chunk_text_for_rag
from app.services.vector_store import get_vector_store

router = APIRouter()

UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not (file.filename.endswith('.pdf') or file.filename.endswith('.txt')):
        raise HTTPException(status_code=400, detail="Invalid file type.")
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    collection_name = "".join(ch for ch in file.filename if ch.isalnum()).lower()
    # Extract text
    if file.filename.endswith('.pdf'):
        text = extract_text_from_pdf(str(file_path))
    else:
        text = Path(file_path).read_text(encoding="utf-8")
    chunks = chunk_text_for_rag(text)
    vector_store = get_vector_store(collection_name=collection_name)
    vector_store.add_texts(chunks)
    return {"filename": file.filename, "collection_name": collection_name, "total_chunks": len(chunks), "filePath": str(file_path)}
