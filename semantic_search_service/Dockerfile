# =========================
# Stage 1: Builder
# =========================
FROM python:3.13-slim AS builder
WORKDIR /app

COPY requirements.txt .

# Install all dependencies for downloading models
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

RUN mkdir -p /app/models

# Copy the model download script and execute it
COPY download_models.py .
RUN python download_models.py

# Clean caches to reduce image size
RUN rm -rf ~/.cache/pip ~/.cache/huggingface

# =========================
# Stage 2: Final image
# =========================
FROM python:3.13-slim
WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy only the models from the builder
COPY --from=builder /app/models /app/models

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
