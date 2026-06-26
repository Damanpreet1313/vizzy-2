from fastapi import APIRouter, Form, HTTPException
import os
from app.services.text_engine import extract_text_from_pdf, chunk_text_uniform
from app.graphs.auto_graph import auto_mode_graph

router = APIRouter()

@router.post("/auto-mode")
async def run_auto_mode(file_path: str = Form(...), total_frames: int = Form(...)):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Target text source file not found.")
    if file_path.endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    segments = chunk_text_uniform(text, total_frames)
    initial_state = {
        "text_segments": segments,
        "current_index": 0,
        "total_frames": total_frames,
        "collection": []
    }
    result = auto_mode_graph.invoke(initial_state)
    return {"collection": result["collection"]}
