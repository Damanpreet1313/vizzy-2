# ── Backend Dockerfile ──────────────────────────────────────────────────────
FROM python:3.11-slim

# System deps needed by some ML packages (pdfplumber, grpcio, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create data directories
RUN mkdir -p ./data/uploads

# Expose port
EXPOSE 8000

# Run with a single worker (Milvus Lite requires single-process)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
