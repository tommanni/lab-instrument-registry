from fastapi.testclient import TestClient
import numpy as np
from main import app, MAX_BATCH_SIZE

client = TestClient(app)

def test_health_check():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_process_text():
    payload = {"text": "test input"}
    response = client.post("/process", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "translated_text" in data
    assert data["translated_text"] == "mock translated text"
    assert "embedding_en" in data
    assert data["embedding_en"] == [0.1, 0.2, 0.3]

def test_process_text_translation_failure(mocker):
    """
    Test /process endpoint when translation fails.
    Should return translated_text="translation failed" and embedding_en=None.
    """
    # Patch the function imported in main.py
    mocker.patch("main.translate_fi_to_en", return_value="Translation Failed")

    payload = {"text": "test input"}
    response = client.post("/process", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["translated_text"] == "translation failed"
    assert data["embedding_en"] is None

def test_process_batch_success():
    payload = {"texts": ["text1", "text2"]}
    response = client.post("/process_batch", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) == 2
    for item in data:
        assert item["translated_text"] == "mock translated text"
        assert item["embedding_en"] == [0.1, 0.2, 0.3]

def test_process_batch_mixed_results(mocker):
    """
    Test /process_batch with mixed success/failure in translation.
    """
    # Mock translation to return 1 success, 1 failure
    mocker.patch(
        "main.translate_fi_to_en_batch", 
        return_value=["valid translation", "Translation Failed"]
    )
    
    # Mock embedding batch to return only 1 embedding (since only 1 valid translation)
    # The service logic should map this single embedding to the valid item
    # and assign None to the failed item.
    mocker.patch(
        "main.embed_en_batch",
        return_value=np.array([[0.9, 0.9, 0.9]])
    )

    payload = {"texts": ["text1", "text2"]}
    response = client.post("/process_batch", json=payload)

    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    
    # Item 1: Success
    assert data[0]["translated_text"] == "valid translation"
    assert data[0]["embedding_en"] == [0.9, 0.9, 0.9]

    # Item 2: Failure
    assert data[1]["translated_text"] == "translation failed"
    assert data[1]["embedding_en"] is None

def test_process_batch_empty_list():
    """Test /process_batch with empty list input."""
    payload = {"texts": []}
    response = client.post("/process_batch", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_process_batch_limit():
    # Create a list slightly larger than the limit
    oversized_list = ["text"] * (MAX_BATCH_SIZE + 1)
    payload = {"texts": oversized_list}
    
    response = client.post("/process_batch", json=payload)
    
    assert response.status_code == 413
    assert "Maximum batch size" in response.json()["detail"]

def test_embed_en():
    payload = {"text": "english text"}
    response = client.post("/embed_en", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "embedding" in data
    assert data["embedding"] == [0.1, 0.2, 0.3]