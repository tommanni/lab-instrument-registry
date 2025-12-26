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

@app.post("/process_batch")
async def process_batch_text(input_texts: InputTexts):
    """Batch process multiple texts for translations and embeddings"""
    if len(input_texts.texts) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Payload too large. Maximum batch size is {MAX_BATCH_SIZE}."
        )

    prefix_texts = [CONTEXT_PREFIX + text.strip().lower() for text in input_texts.texts]

    # Batch translate all Finnish texts to English
    translated_texts = translate_fi_to_en_batch(prefix_texts)

    # Generate English embeddings only for successful translations
    raw_valid_translations = [t for t in translated_texts if t != "Translation Failed"]
    if raw_valid_translations:
        prefixed_valid_translations = [CONTEXT_PREFIX_EN + t for t in raw_valid_translations]
        embeddings_en_valid = embed_en_batch(prefixed_valid_translations, EMBEDDING_BATCH_SIZE)
        # Build dictionary for quick lookup
        en_embeddings_dict = {
            text: emb.tolist() for text, emb in zip(raw_valid_translations, embeddings_en_valid)
        }
    else:
        en_embeddings_dict = {}

    # Combine results
    results = []
    for i, (_, translated_text) in enumerate(zip(input_texts.texts, translated_texts)):
        results.append({
            "translated_text": translated_text.lower(),
            "embedding_en": en_embeddings_dict.get(translated_text)
            if translated_text != "Translation Failed" else None,
        })

    # Delete all intermediate variables
    del en_embeddings_dict, translated_texts, prefix_texts
    cleanup_memory()

    return results

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

@app.post("/translate_batch")
async def translate_batch_endpoint(input_texts: InputTexts):
    prefixed_texts = [
        CONTEXT_PREFIX + text.strip()
        for text in input_texts.texts
    ]
    translations = translate_fi_to_en_batch(prefixed_texts)
    return {"translations": translations}