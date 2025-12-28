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

def test_embed_en():
    payload = {"text": "english text"}
    response = client.post("/embed_en", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "embedding" in data
    assert data["embedding"] == [0.1, 0.2, 0.3]