FROM python:3.12-slim

# gcc + libffi needed by cryptography/passlib native extensions
# curl needed for HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libffi-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first — this layer is cached separately from source code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source (respects .dockerignore)
COPY . .

# Pre-create runtime directories (named volumes will mount over these at run time)
RUN mkdir -p uploads/rooms uploads/assignments

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
