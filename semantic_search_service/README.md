# Semantic Search Service

CPU-only FastAPI microservice that translates Finnish instrument names to English and generates embeddings for both languages. The Django backend reaches it over Docker Compose (`http://semantic-search-service:8001`).

## Stack

- **FastAPI + Uvicorn** for the HTTP API  
- **SentenceTransformer** (`BAAI/bge-base-en-v1.5`) for embeddings  
- **Helsinki-NLP/opus-mt-fi-en** (fine-tuned) for Finnish→English translation  
- **PyTorch (CPU)** with dynamic quantization for smaller memory footprint and faster inference

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/process` | Translate a single Finnish string and generate embeddings (`embedding_en`). |
| `POST` | `/process_batch` | Batch version of `/process` (up to `MAX_BATCH_SIZE` = 256). |
| `POST` | `/embed_en` | English embedding only. |
| `GET` | `/healthz` | Returns `{"status": "ok"}` once all models are loaded (used by Docker healthcheck). |

## Model Handling

- Model IDs are resolved at startup:
  - Translation model: `FINE_TUNED_OPUS_MT_ID` env var (defaults to `Helsinki-NLP/opus-mt-fi-en`).
  - Local paths (mounted via volume): `/app/models/<model-name>`.
- Models are **lazy-loaded** in `models.py` the first time they’re requested. `warm_up_models()` runs at FastAPI `startup` and issues tiny dummy requests so the first user call does not pay the initialization cost.
- `download_models.py` populates `/app/models` and is run automatically from the Docker CMD before Uvicorn starts. On a fresh volume, expect the first boot to spend a while downloading weights; subsequent boots reuse the cached models.

## Local Development

```bash
make semantic-search
```

The container:
1. Installs requirements (CPU wheels only).
2. Runs `python download_models.py` to ensure weights exist under `/app/models`.
3. Starts `uvicorn main:app --reload`.

Hot reload is enabled; changes under `semantic_search_service/` trigger Uvicorn restart.

## Health & Operations

- Docker Compose defines a healthcheck:
  ```yaml
  healthcheck:
    test: ["CMD-SHELL", "curl -fsS http://localhost:8001/healthz || exit 1"]
    interval: 60s
    timeout: 5s
    retries: 5
    start_period: 30s
  ```
  and `restart: unless-stopped`, so unhealthy containers restart automatically.
- Resource controls: `torch.set_num_threads(n)` and environment variables limit CPU thread usage.
- Everything runs on CPU; no CUDA dependencies are required.

## Updating Models

1. Update `FINE_TUNED_OPUS_MT_ID` in `docker-compose.yml` (or inject via env).
2. Stop/remove the semantic-search-service container.
3. Delete the `semantic-models-data` volume if you need to redownload weights.
4. `docker compose up` to rebuild and warm the new models.

## Running Outside Docker

```bash
cd semantic_search_service
python -m venv .venv && source .venv/bin/activate
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
python download_models.py
uvicorn main:app --reload
```

Set `FINE_TUNED_OPUS_MT_ID` in your shell if you want a custom translation model.

## Testing

The service includes a comprehensive test suite covering both unit logic and API endpoints. To ensure fast execution without loading heavy ML models, all tests use mocked models by default.

### Running Tests

#### Option 1: Docker (Recommended)
Run tests inside the container using the project Makefile:
```bash
make semantic-test
```
This requires the service to be running (`make semantic-search`).

#### Option 2: Manual (Local Environment)
1.  **Activate your virtual environment** (see "Running Outside Docker" above).
2.  **Install test dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the tests:**
    ```bash
    pytest
    ```

### Test Structure

*   `tests/conftest.py`: Contains global fixtures, including mocks for the `MarianMT` (translation) and `SentenceTransformer` (embedding) models.
*   `tests/test_services.py`: Unit tests for core logic (prefix handling, validation, batch processing).
*   `tests/test_main.py`: Integration tests for the FastAPI endpoints (`/process`, `/process_batch`, `/healthz`).
