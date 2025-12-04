import pytest
from services import (
    _strip_context_prefix,
    translate_fi_to_en,
    translate_fi_to_en_batch,
    embed_en,
    embed_en_batch,
    PREFIX
)

# ==========================================================
# Helper Function Tests
# ==========================================================
def test_strip_context_prefix():
    # Exact match
    assert _strip_context_prefix(PREFIX + "test") == "test"
    # Case insensitive match
    assert _strip_context_prefix(PREFIX.upper() + "TEST") == "TEST"
    # No prefix
    assert _strip_context_prefix("just some text") == "just some text"
    # Partial prefix (should not strip)
    assert _strip_context_prefix("scientific") == "scientific"
    # Empty string
    assert _strip_context_prefix("") == ""
    # Only prefix
    assert _strip_context_prefix(PREFIX) == ""
    # Prefix with extra spaces
    assert _strip_context_prefix(PREFIX + "  test  ") == "test  "
    # Multiple prefixes (should only strip first)
    assert _strip_context_prefix(PREFIX + PREFIX + "test") == PREFIX + "test"
    # Prefix at end of string (should not strip)
    assert _strip_context_prefix("test" + PREFIX) == "test" + PREFIX

# ==========================================================
# Translation Tests
# ==========================================================
def test_translate_fi_to_en_success(mocker):
    # The mock in conftest.py ensures this returns "mock translated text"
    result = translate_fi_to_en("test text")
    assert result == "mock translated text"

def test_translate_fi_to_en_exception(mocker):
    # Force an exception in the translation process
    mocker.patch("services.get_translation_components", side_effect=Exception("Model crash"))

    result = translate_fi_to_en("test text")
    assert result == "Translation Failed"

def test_translate_fi_to_en_sanity_check_fail(mocker):
    # Mock the tokenizer.decode to return a string that is too long
    # Input: "a", Result: "aaaa" (length 4 > 3 * 1)

    mock_tokenizer = mocker.Mock()
    mock_tokenizer.return_value = {"input_ids": [], "attention_mask": []}
    # decode returns a long string
    mock_tokenizer.decode.return_value = "aaaa"

    mock_model = mocker.Mock()
    mock_model.generate.return_value = [1]

    mocker.patch("services.get_translation_components", return_value=(mock_tokenizer, mock_model))

    result = translate_fi_to_en("a")
    assert result == "Translation Failed"

def test_translate_fi_to_en_empty_input(mocker):
    # Test with empty string input
    result = translate_fi_to_en("")
    assert result == "Translation Failed"

def test_translate_fi_to_en_none_input(mocker):
    # Test with None-like input (should be handled by strip)
    result = translate_fi_to_en("   ")
    assert result == "Translation Failed"  # Empty after stripping

def test_translate_fi_to_en_special_characters(mocker):
    # Test with special characters and unicode
    special_input = "test!@#$%^&*()_+{}|:<>?[]"
    result = translate_fi_to_en(special_input)
    assert isinstance(result, str)  # Should return a string even if failed

def test_translate_fi_to_en_batch_empty_list(mocker):
    # Test batch translation with empty list
    results = translate_fi_to_en_batch([])
    assert results == []

def test_translate_fi_to_en_batch_success():
    texts = ["longer input text 1", "longer input text 2"]
    results = translate_fi_to_en_batch(texts)
    assert len(results) == 2
    assert all(r == "mock translated text" for r in results)

def test_translate_fi_to_en_batch_exception(mocker):
    mocker.patch("services.get_translation_components", side_effect=Exception("Batch crash"))
    texts = ["text1", "text2"]
    results = translate_fi_to_en_batch(texts)

    assert len(results) == 2
    assert all(r == "Translation Failed" for r in results)

def test_translate_fi_to_en_batch_sanity_check_mixed(mocker):
    """
    Test batch translation where one item is valid and another 
    fails the length sanity check.
    """
    # Input texts: "a" (short), "valid input" (normal)
    # We want "a" to map to "aaaa" (fail: 4 > 3*1)
    # and "valid input" to map to "ok" (pass)
    
    mock_tokenizer = mocker.Mock()
    # tokenizer call return (tokens)
    mock_tokenizer.return_value = {"input_ids": [1, 2], "attention_mask": [1, 1]}
    
    # batch_decode return
    # Index 0 corresponds to "a", Index 1 corresponds to "valid input"
    mock_tokenizer.batch_decode.return_value = ["aaaa", "ok"]

    mock_model = mocker.Mock()
    mock_model.generate.return_value = [1, 2] # Dummy

    mocker.patch("services.get_translation_components", return_value=(mock_tokenizer, mock_model))

    texts = ["a", "valid input"]
    results = translate_fi_to_en_batch(texts)

    assert len(results) == 2
    assert results[0] == "Translation Failed" # "aaaa" is too long for "a"
    assert results[1] == "ok"

# ==========================================================
# Embedding Tests
# ==========================================================
def test_embed_en_success():
    result = embed_en("some text")
    assert isinstance(result, list)
    assert len(result) == 3
    assert result == [0.1, 0.2, 0.3]

def test_embed_en_batch_success():
    texts = ["text1", "text2"]
    results = embed_en_batch(texts)

    assert len(results) == 2
    # Check that it returns a numpy array or list of lists (the mock returns np array)
    assert results.shape == (2, 3)
    assert results[0].tolist() == [0.1, 0.2, 0.3]
