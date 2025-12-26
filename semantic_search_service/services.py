from typing import List
import gc
import torch
from models import (
    get_translation_components,
    get_embedding_model_en,
    logger,
)

PREFIX = "scientific instrument: "

def _strip_context_prefix(text: str) -> str:
    """Remove the known translation prefix if it appears at the beginning."""
    normalized = text.lower()
    if normalized.startswith(PREFIX):
        return text[len(PREFIX):].lstrip()
    return text


# ==========================================================
# Translation Functions
# ==========================================================
def translate_fi_to_en(text: str) -> str:
    try:
        tokenizer, model = get_translation_components()
        tokens = tokenizer(text, return_tensors="pt", padding=True)
        translated = model.generate(**tokens)
        result = tokenizer.decode(translated[0], skip_special_tokens=True).strip()
        if len(result) > 3 * len(text):
            return "Translation Failed"
        result = _strip_context_prefix(result)
        return result
    except Exception as e:
        logger.error(f"Translation failed for text: '{text}'. Error: {e}", exc_info=True)
        return "Translation Failed"

def translate_fi_to_en_batch(texts: List[str]) -> List[str]:
    """Batch translate Finnish texts to English efficiently"""
    try:
        tokenizer, model = get_translation_components()
        # Tokenize all input texts at once
        tokens = tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True
        )

        # Generate all translations
        translated = model.generate(**tokens)

        # Batch decode all generated sequences
        decoded_texts = tokenizer.batch_decode(
            translated,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        )

        # Clean up tensors immediately
        del tokens, translated

        # Translation cleanup and validation
        results = []
        for original, result in zip(texts, decoded_texts):
            result = result.strip()
            if len(result) > 3 * len(original) or len(result) > 100:
                result = "Translation Failed"
            else:
                result = _strip_context_prefix(result)
            results.append(result)

        return results

    except Exception as e:
        logger.error(f"Batch translation failed for {len(texts)} texts. Error: {e}", exc_info=True)
        # Return failure for all if translation fails
        return ["Translation Failed"] * len(texts)

# ==========================================================
# Embedding Functions
# ==========================================================
def embed_en(text: str) -> list:
    """Generate English embedding for a single text"""
    model = get_embedding_model_en()
    return model.encode(text, normalize_embeddings=True).tolist()

def embed_en_batch(texts: List[str], batch_size: int = 100) -> list:
    """Generate English embeddings for multiple texts"""
    model = get_embedding_model_en()
    return model.encode(
        texts,
        batch_size=batch_size, 
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

# ==========================================================
# Memory Cleanup
# ==========================================================
def cleanup_memory():
    """Force memory cleanup garbage collection"""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    # Force Python garbage collection
    gc.collect(2)  # Full collection
