from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import List
from models import (
    MAX_BATCH_SIZE,
    CONTEXT_PREFIX,
    CONTEXT_PREFIX_EN,
    EMBEDDING_BATCH_SIZE,
    BGE_INSTRUCTION,
    warm_up_models,
    ensure_models_loaded,
)
from services import (
    translate_fi_to_en,
    translate_fi_to_en_batch,
    embed_en,
    embed_en_batch,
    cleanup_memory
)

app = FastAPI()

@app.on_event("startup")
async def load_models_on_startup():
    """Preload and warm models before accepting requests."""
    await run_in_threadpool(warm_up_models)


@app.get("/healthz", tags=["health"])
async def health_check():
    """Report readiness once models are available."""
    ensure_models_loaded()
    return {"status": "ok"}

# ==========================================================
# Pydantic Schemas
# ==========================================================
class InputText(BaseModel):
    text: str

class InputTexts(BaseModel):
    texts: List[str]

# ==========================================================
# Endpoints
# ==========================================================
@app.post("/process")
async def process_text(input_text: InputText):
    fi_text = input_text.text.strip().lower()

    translated_text = translate_fi_to_en(CONTEXT_PREFIX + fi_text)

    embedding_en_result = (
        embed_en(CONTEXT_PREFIX_EN + translated_text)
        if translated_text != "Translation Failed"
        else None
    )

    return {
        "translated_text": translated_text.lower(),
        "embedding_en": embedding_en_result,
    }

@app.post("/process_query")
async def process_query_endpoint(input_text: InputText):
    """Process queries that need to be translated to English and then embedded"""
    fi_text = input_text.text.strip().lower()

    translated_text = translate_fi_to_en(CONTEXT_PREFIX + fi_text)

    if translated_text == "Translation Failed":
        return {
            "translated_text": None, 
            "embedding_en": None
        }

    query_text = translated_text
    if not query_text.startswith("Represent this sentence"):
        query_text = BGE_INSTRUCTION + query_text

    embedding_en_result = embed_en(query_text)

    return {
        "translated_text": translated_text.lower(),
        "embedding_en": embedding_en_result,
    }

@app.post("/embed_en")
async def embed_en_endpoint(input_text: InputText):
    embedding = embed_en(input_text.text.strip())
    return {"embedding": embedding}

@app.post("/embed_query")
async def embed_query_endpoint(input_text: InputText):    
    query = input_text.text.strip()
    if not query.startswith("Represent this sentence"):
        query = BGE_INSTRUCTION + query
        
    embedding = embed_en(query)
    return {"embedding": embedding}

@app.post("/embed_en_batch")
async def embed_en_batch_endpoint(input_texts: InputTexts):
    clean_texts = [text.strip() for text in input_texts.texts]
    
    embeddings = embed_en_batch(clean_texts, EMBEDDING_BATCH_SIZE)
    return {"embeddings": embeddings.tolist()}
