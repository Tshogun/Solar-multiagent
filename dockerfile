# Use slim Python image
FROM python:3.10-slim

WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements-light.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY sample_pdfs/ ./sample_pdfs/
COPY .env.example .env

# Create required folders
RUN mkdir -p data/uploads data/faiss_index logs

# Set environment variables for memory optimization
ENV PYTHONUNBUFFERED=1
ENV SENTENCE_TRANSFORMERS_HOME=/tmp/models
ENV TRANSFORMERS_CACHE=/tmp/transformers

# Expose port (Render sets this via env var)
EXPOSE 8000

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with reduced worker count for memory efficiency
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]