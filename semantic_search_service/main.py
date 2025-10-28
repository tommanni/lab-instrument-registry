from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import List
from models import (
    MAX_BATCH_SIZE,
    CONTEXT_PREFIX,
    CONTEXT_PREFIX_EN,
    EMBEDDING_BATCH_SIZE,
    warm_up_models,
    ensure_models_loaded,
)
from services import (
    translate_fi_to_en,
    translate_fi_to_en_batch,
    embed_fi,
    embed_en,
    embed_fi_batch,
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

    # Translate text
    translated_text = translate_fi_to_en(CONTEXT_PREFIX + fi_text)

    # Generate embeddings
    embedding_fi_result = embed_fi(CONTEXT_PREFIX + fi_text)
    embedding_en_result = (
        embed_en(CONTEXT_PREFIX_EN + translated_text)
        if translated_text != "Translation Failed"
        else None
    )

    return {
        "translated_text": translated_text.lower(),
        "embedding_fi": embedding_fi_result,
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

    # Generate Finnish embeddings
    embeddings_fi = embed_fi_batch(prefix_texts, EMBEDDING_BATCH_SIZE)
    
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
            "embedding_fi": embeddings_fi[i].tolist(),
            "embedding_en": en_embeddings_dict.get(translated_text)
            if translated_text != "Translation Failed" else None,
        })

    # Delete all intermediate variables
    del embeddings_fi, en_embeddings_dict, translated_texts, prefix_texts
    cleanup_memory()

    return results

@app.post("/embed_fi")
async def embed_fi_endpoint(input_text: InputText):
    embedding = embed_fi(CONTEXT_PREFIX + input_text.text.strip().lower())
    return {"embedding": embedding}

@app.post("/embed_en")
async def embed_en_endpoint(input_text: InputText):
    embedding = embed_en(CONTEXT_PREFIX_EN + input_text.text.strip().lower())
    return {"embedding": embedding}
