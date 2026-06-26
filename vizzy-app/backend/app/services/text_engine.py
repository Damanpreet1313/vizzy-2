import pdfplumber
from typing import List

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts raw text from a PDF file using pdfplumber."""
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
    return "\n".join(full_text)

def chunk_text_uniform(text: str, n: int) -> List[str]:
    """Divides text into exactly n sequential uniform segments by words."""
    words = text.split()
    total_words = len(words)
    if total_words == 0:
        return [""] * n
    
    chunk_size = max(1, total_words // n)
    chunks = []
    
    for i in range(n):
        start_idx = i * chunk_size
        # For the last chunk, take all remaining words
        if i == n - 1:
            chunk_words = words[start_idx:]
        else:
            chunk_words = words[start_idx:start_idx + chunk_size]
        chunks.append(" ".join(chunk_words))
        
    return chunks

def chunk_text_for_rag(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Chunks text into small semantic pieces with overlap for Milvus RAG."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += (chunk_size - overlap)
    return chunks
