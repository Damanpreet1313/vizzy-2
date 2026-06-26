import sys
import os
from unittest.mock import MagicMock, patch

# Ensure the backend directory is in the python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

# Mock environmental dependencies to prevent initializations during import
with patch.dict(os.environ, {"GROQ_API_KEY": "dummy_key", "OPENAI_API_KEY": "dummy_key"}):
    from app.main import app

client = TestClient(app)

# ==========================================
# 1. Tests for /api/upload
# ==========================================

@patch("app.main.os.makedirs")
@patch("app.main.open")
@patch("app.main.shutil.copyfileobj")
@patch("app.main.extract_text_from_pdf")
@patch("app.main.chunk_text_for_rag")
@patch("app.main.get_vector_store")
def test_upload_pdf_success(
    mock_get_vector_store,
    mock_chunk_for_rag,
    mock_extract_pdf,
    mock_copyfileobj,
    mock_open,
    mock_makedirs
):
    # Mock text extraction and chunking
    mock_extract_pdf.return_value = "Page content of PDF."
    mock_chunk_for_rag.return_value = ["chunk 1", "chunk 2"]

    # Mock vector store
    mock_store = MagicMock()
    mock_get_vector_store.return_value = mock_store

    # Call upload endpoint
    pdf_content = b"%PDF-1.4 dummy content"
    files = {"file": ("test_doc.pdf", pdf_content, "application/pdf")}
    response = client.post("/api/upload", files=files)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["filename"] == "test_doc.pdf"
    assert res_data["collection_name"] == "testdoc"
    assert res_data["total_chunks"] == 2

    # Verify vector store operations were triggered
    mock_get_vector_store.assert_called_once_with(collection_name="testdoc")
    mock_store.add_texts.assert_called_once_with(["chunk 1", "chunk 2"])

def test_upload_invalid_file_type():
    files = {"file": ("document.docx", b"dummy docx content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


# ==========================================
# 2. Tests for /api/auto-mode
# ==========================================

@patch("app.main.os.path.exists")
@patch("app.main.extract_text_from_pdf")
@patch("app.main.chunk_text_uniform")
@patch("app.main.auto_mode_graph")
def test_run_auto_mode_success(
    mock_auto_graph,
    mock_chunk_uniform,
    mock_extract_pdf,
    mock_path_exists
):
    # File exists check
    mock_path_exists.return_value = True
    
    # Mock text processing
    mock_extract_pdf.return_value = "PDF book content."
    mock_chunk_uniform.return_value = ["segment 1", "segment 2", "segment 3"]

    # Mock graph invoke
    mock_result = {
        "collection": [
            {"frame_index": 0, "image_url": "url1", "prompt": "prompt1"},
            {"frame_index": 1, "image_url": "url2", "prompt": "prompt2"},
            {"frame_index": 2, "image_url": "url3", "prompt": "prompt3"},
        ]
    }
    mock_auto_graph.invoke.return_value = mock_result

    # Call endpoint
    payload = {"file_path": "./data/uploads/sample.pdf", "total_frames": 3}
    response = client.post("/api/auto-mode", data=payload)

    assert response.status_code == 200
    res_data = response.json()
    assert "collection" in res_data
    assert len(res_data["collection"]) == 3
    assert res_data["collection"][0]["frame_index"] == 0
    assert res_data["collection"][0]["image_url"] == "url1"

    # Verify parameters sent to graph
    mock_auto_graph.invoke.assert_called_once_with({
        "text_segments": ["segment 1", "segment 2", "segment 3"],
        "current_index": 0,
        "total_frames": 3,
        "collection": []
    })

@patch("app.main.os.path.exists")
def test_run_auto_mode_file_not_found(mock_path_exists):
    mock_path_exists.return_value = False
    payload = {"file_path": "./data/uploads/nonexistent.pdf", "total_frames": 5}
    response = client.post("/api/auto-mode", data=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Target text source file not found."


# ==========================================
# 3. Tests for /api/pilot-mode
# ==========================================

@patch("app.main.pilot_mode_graph")
def test_run_pilot_mode_success(mock_pilot_graph):
    # Mock graph invoke response
    mock_result = {
        "chat_reply": "According to the story, the hero went west.",
        "generated_image_url": "https://image.pollinations.ai/prompt/hero_going_west"
    }
    mock_pilot_graph.invoke.return_value = mock_result

    # Call endpoint
    payload = {
        "user_query": "Where did the hero go?",
        "collection_name": "hero_adventure"
    }
    response = client.post("/api/pilot-mode", json=payload)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["reply"] == "According to the story, the hero went west."
    assert res_data["imageUrl"] == "https://image.pollinations.ai/prompt/hero_going_west"

    # Verify parameters sent to graph
    mock_pilot_graph.invoke.assert_called_once_with({
        "user_query": "Where did the hero go?",
        "collection_name": "hero_adventure",
        "chat_reply": "",
        "generated_image_url": ""
    })
