import logging
import os
import sys
import threading

import torch
from sentence_transformers import SentenceTransformer
from transformers import MarianMTModel, MarianTokenizer

# ==========================================================
# Configuration
# ==========================================================

MAX_BATCH_SIZE = 256
CONTEXT_PREFIX = "tieteellinen instrumentti: "
CONTEXT_PREFIX_EN = "a scientific instrument: "
EMBEDDING_BATCH_SIZE = 100

# --- Opus MT Model for translation (Fine-tuned or original) ---
fine_tuned_opus_mt_id = os.getenv("FINE_TUNED_OPUS_MT_ID")
opus_mt_model_name = fine_tuned_opus_mt_id if fine_tuned_opus_mt_id else "Helsinki-NLP/opus-mt-fi-en"
sanitized_model_name = opus_mt_model_name.replace("/", "_")

# Model paths
TRANSLATION_MODEL_PATH = f"/app/models/{sanitized_model_name}"
EMBEDDING_MODEL_FI_PATH = "/app/models/sbert-uncased-finnish-paraphrase"
EMBEDDING_MODEL_EN_PATH = "/app/models/all-mpnet-base-v2"

# ==========================================================
# Logging setup
# ==========================================================

log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(log_formatter)
    logger.addHandler(handler)

# ==========================================================
# CPU and memory optimization settings
# ==========================================================

torch.set_grad_enabled(False)

torch.set_num_threads(3)  # Adjust based on available cores
# Limit thread usage to prevent memory bloat
os.environ["OMP_NUM_THREADS"] = "3"
os.environ["MKL_NUM_THREADS"] = "3"

# ==========================================================
# Lazy model registry
# ==========================================================

_translation_tokenizer = None
_translation_model = None
_embedding_model_fi = None
_embedding_model_en = None
_models_loaded = False
_models_lock = threading.Lock()


def _load_translation_components():
    global _translation_tokenizer, _translation_model

    logger.info("Loading translation tokenizer from %s", TRANSLATION_MODEL_PATH)
    _translation_tokenizer = MarianTokenizer.from_pretrained(
        TRANSLATION_MODEL_PATH,
        local_files_only=True
    )

    logger.info("Loading translation model from %s", TRANSLATION_MODEL_PATH)
    translation_model = MarianMTModel.from_pretrained(
        TRANSLATION_MODEL_PATH,
        local_files_only=True
    )

    logger.info("Quantizing translation model for CPU inference")
    translation_model = torch.quantization.quantize_dynamic(
        translation_model,
        {torch.nn.Linear, torch.nn.LSTM, torch.nn.GRU},
        dtype=torch.qint8
    )
    translation_model.eval()

    _translation_model = translation_model


def _load_embedding_models():
    global _embedding_model_fi, _embedding_model_en

    logger.info("Loading Finnish embedding model from %s", EMBEDDING_MODEL_FI_PATH)
    _embedding_model_fi = SentenceTransformer(
        EMBEDDING_MODEL_FI_PATH,
        local_files_only=True,
        device='cpu'
    )
    _embedding_model_fi.eval()

    logger.info("Loading English embedding model from %s", EMBEDDING_MODEL_EN_PATH)
    _embedding_model_en = SentenceTransformer(
        EMBEDDING_MODEL_EN_PATH,
        local_files_only=True,
        device='cpu'
    )
    _embedding_model_en.eval()


def ensure_models_loaded():
    """Load all models once in a thread-safe manner."""
    global _models_loaded

    if _models_loaded:
        return

    with _models_lock:
        if _models_loaded:
            return

        logger.info("Initializing translation and embedding models")
        _load_translation_components()
        _load_embedding_models()
        _models_loaded = True
        logger.info("All models loaded successfully")


def get_translation_components():
    ensure_models_loaded()
    return _translation_tokenizer, _translation_model


def get_embedding_model_fi():
    ensure_models_loaded()
    return _embedding_model_fi


def get_embedding_model_en():
    ensure_models_loaded()
    return _embedding_model_en


def warm_up_models():
    """Run inexpensive dummy requests so first real request is fast."""
    ensure_models_loaded()

    try:
        tokenizer, model = get_translation_components()
        sample = tokenizer(CONTEXT_PREFIX + "testi", return_tensors="pt")
        _ = model.generate(**sample)
    except Exception as exc:
        logger.warning("Translation warm-up failed: %s", exc)

    try:
        get_embedding_model_fi().encode(["testi"], show_progress_bar=False)
        get_embedding_model_en().encode(["device"], show_progress_bar=False)
    except Exception as exc:
        logger.warning("Embedding warm-up failed: %s", exc)


__all__ = [
    "MAX_BATCH_SIZE",
    "CONTEXT_PREFIX",
    "CONTEXT_PREFIX_EN",
    "EMBEDDING_BATCH_SIZE",
    "ensure_models_loaded",
    "warm_up_models",
    "get_translation_components",
    "get_embedding_model_fi",
    "get_embedding_model_en",
    "logger",
]
