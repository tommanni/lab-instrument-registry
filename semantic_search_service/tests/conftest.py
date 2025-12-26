import pytest
import torch
from unittest.mock import MagicMock
import numpy as np

# ==========================================================
# Mocks for Translation
# ==========================================================
class MockTokenizer:
    def __call__(self, texts, return_tensors="pt", padding=True, truncation=True):
        # Return dummy tensors
        count = 1
        if isinstance(texts, list):
            count = len(texts)
        
        # Create a tensor with 'count' rows
        return {
            "input_ids": torch.tensor([[1, 2, 3]] * count),
            "attention_mask": torch.tensor([[1, 1, 1]] * count)
        }

    def decode(self, token_ids, skip_special_tokens=True):
        return "mock translated text"

    def batch_decode(self, token_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True):
        # Return a list of strings equal to the number of "rows" in the input
        # For the mock, we assume the input is the result of MockTranslationModel.generate
        return ["mock translated text"] * len(token_ids)


class MockTranslationModel:
    def generate(self, **kwargs):
        # Return dummy token IDs. 
        # If inputs were batched, we should return multiple rows.
        # We'll infer batch size from input_ids if present, else default to 1.
        input_ids = kwargs.get("input_ids")
        batch_size = input_ids.shape[0] if input_ids is not None else 1
        return torch.tensor([[10, 11, 12]] * batch_size)


# ==========================================================
# Mocks for Embeddings
# ==========================================================
class MockEmbeddingModel:
    def encode(self, sentences, batch_size=32, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True):
        # Return fixed embeddings
        # If input is a single string, return 1D array
        if isinstance(sentences, str):
            return np.array([0.1, 0.2, 0.3], dtype=np.float64)
        # If input is a list, return 2D array
        return np.array([[0.1, 0.2, 0.3] for _ in sentences], dtype=np.float64)


# ==========================================================
# Fixtures
# ==========================================================
@pytest.fixture(autouse=True)
def mock_ml_models(mocker):
    """
    Automatically mock the heavy ML loading functions for all tests.
    """
    # Mock translation components
    mock_tokenizer = MockTokenizer()
    mock_translation_model = MockTranslationModel()
    
    # Patch in models module (definition source)
    mocker.patch(
        "models.get_translation_components",
        return_value=(mock_tokenizer, mock_translation_model)
    )
    # Patch in services module (usage source)
    mocker.patch(
        "services.get_translation_components",
        return_value=(mock_tokenizer, mock_translation_model)
    )

    # Mock embedding model
    mock_embedding_model = MockEmbeddingModel()
    # Patch in models module (definition source)
    mocker.patch(
        "models.get_embedding_model_en",
        return_value=mock_embedding_model
    )
    # Patch in services module (usage source)
    mocker.patch(
        "services.get_embedding_model_en",
        return_value=mock_embedding_model
    )

    # Prevent actual model warming and ensure_models_loaded
    mocker.patch("models.warm_up_models")
    mocker.patch("models.ensure_models_loaded")
    mocker.patch("main.warm_up_models")
    mocker.patch("main.ensure_models_loaded")
