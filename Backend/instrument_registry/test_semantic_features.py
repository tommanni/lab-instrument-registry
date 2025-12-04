from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from instrument_registry.models import Instrument, RegistryUser
from instrument_registry.embedding import precompute_instrument_embeddings
from instrument_registry.util import should_translate_to_english
from pgvector.django import CosineDistance
import requests

class LanguageDetectionTest(TestCase):
    """Test language detection utility function"""

    def test_should_translate(self):
        """Test that Finnish text triggers translation while English does not"""
        # Finnish -> True
        self.assertTrue(should_translate_to_english("Mikroskooppi"))
        self.assertTrue(should_translate_to_english("Tämä on suomenkielinen lause"))

        # English -> False
        self.assertFalse(should_translate_to_english("Microscope"))
        self.assertFalse(should_translate_to_english("This is an english sentence"))

        # Empty/None -> True (Default safe)
        self.assertTrue(should_translate_to_english(""))
        self.assertTrue(should_translate_to_english(None))

class PrecomputeEmbeddingsTest(TestCase):
    """Test the background job for translating and embedding instruments"""

    def setUp(self):
        # Create some sample instruments
        self.inst1 = Instrument.objects.create(
            tuotenimi="Mikroskooppi",
            tuotenimi_en="",
            embedding_en=None
        )
        self.inst2 = Instrument.objects.create(
            tuotenimi="Vaaka",
            tuotenimi_en="",
            embedding_en=None
        )
        self.inst3 = Instrument.objects.create(
            tuotenimi="Spectrometer",
            tuotenimi_en="Spectrometer", # Already English/Translated
            embedding_en=None
        )

    @patch('instrument_registry.embedding._requests_retry_session')
    def test_precompute_success(self, mock_session_builder):
        """Test successful batch translation and embedding of instruments"""
        # Mock the session and its post method
        mock_session = MagicMock()
        mock_session_builder.return_value = mock_session

        # Mock responses
        # First call: batch translation
        mock_response_translation = MagicMock()
        mock_response_translation.status_code = 200
        mock_response_translation.json.return_value = [
            {'translated_text': 'Microscope', 'embedding_en': [0.1]*768},
            {'translated_text': 'Scale', 'embedding_en': [0.2]*768}
        ]

        # Second call: embedding for existing English text (inst3)
        mock_response_embedding = MagicMock()
        mock_response_embedding.status_code = 200
        mock_response_embedding.json.return_value = {'embedding': [0.3]*768}

        # Configure side_effect to return different responses for different calls
        # The logic in precompute_instrument_embeddings does:
        # 1. POST /process_batch (for Mikroskooppi, Vaaka)
        # 2. POST /embed_en (for Spectrometer)

        def side_effect(*args, **kwargs):
            url = args[0]
            if 'process_batch' in url:
                return mock_response_translation
            elif 'embed_en' in url:
                return mock_response_embedding
            return MagicMock(status_code=404)

        mock_session.post.side_effect = side_effect

        # Run the function
        results = precompute_instrument_embeddings(batch_size=10)

        # Refresh objects from db
        self.inst1.refresh_from_db()
        self.inst2.refresh_from_db()
        self.inst3.refresh_from_db()

        # Assertions
        self.assertEqual(results['processed_count'], 3) # 2 needing translation + 1 needing embedding

        # Check Inst1
        self.assertEqual(self.inst1.tuotenimi_en, "Microscope")
        self.assertIsNotNone(self.inst1.embedding_en)

        # Check Inst2
        self.assertEqual(self.inst2.tuotenimi_en, "Scale")

        # Check Inst3
        self.assertEqual(self.inst3.tuotenimi_en, "Spectrometer") # Should remain
        self.assertIsNotNone(self.inst3.embedding_en)

    @patch('instrument_registry.embedding._requests_retry_session')
    def test_precompute_service_failure(self, mock_session_builder):
        """Test handling of service failures during precomputation"""
        mock_session = MagicMock()
        mock_session_builder.return_value = mock_session

        # Mock generic failure
        mock_session.post.side_effect = Exception("Connection refused")

        results = precompute_instrument_embeddings()

        self.inst1.refresh_from_db()
        self.assertEqual(self.inst1.tuotenimi_en, "Translation Failed")
        self.assertEqual(results['failed'], 2) # inst1 and inst2 failed translation

    @patch('instrument_registry.embedding._requests_retry_session')
    def test_precompute_partial_cache(self, mock_session_builder):
        """Test that duplicate instrument names are only translated once per batch"""
        # Test that if we have multiple same items, we only translate once
        Instrument.objects.create(tuotenimi="Mikroskooppi", tuotenimi_en="", embedding_en=None) # Duplicate

        mock_session = MagicMock()
        mock_session_builder.return_value = mock_session

        # Mock response for single translation
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Expecting only ONE translation request for "Mikroskooppi" and "Vaaka" (unique names)
        mock_response.json.return_value = [
            {'translated_text': 'Microscope', 'embedding_en': [0.1]*768},
            {'translated_text': 'Scale', 'embedding_en': [0.2]*768}
        ]

        # We also need to handle the embedding request for "Spectrometer"
        mock_embed_response = MagicMock()
        mock_embed_response.status_code = 200
        mock_embed_response.json.return_value = {'embedding': [0.3]*768}

        def side_effect(*args, **kwargs):
            url = args[0]
            if 'process_batch' in url:
                return mock_response
            if 'embed_en' in url:
                return mock_embed_response
            return MagicMock(status_code=404)

        mock_session.post.side_effect = side_effect

        precompute_instrument_embeddings()

        # Verify all Mikroskooppi instances got updated
        microscopes = Instrument.objects.filter(tuotenimi="Mikroskooppi")
        for m in microscopes:
            self.assertEqual(m.tuotenimi_en, "Microscope")


class SearchIntegrationTest(TestCase):
    """Test the semantic search API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = RegistryUser.objects.create_user(email='test@test.com', full_name='Tester', password='pass')
        self.client.force_authenticate(user=self.user) # Use force_authenticate for DRF

        # Create instruments with embeddings
        vec1 = [1.0] + [0.0] * 767
        vec2 = [0.0] + [1.0] * 766 + [0.0]

        self.inst1 = Instrument.objects.create(
            tuotenimi="Mikroskooppi",
            tuotenimi_en="Microscope",
            embedding_en=vec1
        )
        self.inst2 = Instrument.objects.create(
            tuotenimi="Kaukoputki",
            tuotenimi_en="Telescope",
            embedding_en=vec2
        )

    @patch('instrument_registry.views.requests.post')
    @patch('instrument_registry.views.should_translate_to_english')
    def test_search_english_term(self, mock_should_translate, mock_post):
        """Test searching with an English term (direct embedding)"""
        # Search for "Microscope" (English)
        mock_should_translate.return_value = False

        # Mock embedding response for query "Microscope" -> [1, 0, ...]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'embedding': [1.0] + [0.0] * 767}
        mock_post.return_value = mock_response

        url = '/api/instruments/search/?q=Microscope'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.inst1.id)

        # Verify calls
        mock_post.assert_called_with(
            "http://semantic-search-service:8001/embed_en",
            json={"text": "Microscope"},
            timeout=5.0
        )

    @patch('instrument_registry.views.requests.post')
    @patch('instrument_registry.views.should_translate_to_english')
    def test_search_finnish_term(self, mock_should_translate, mock_post):
        """Test searching with a Finnish term (translation + embedding)"""
        # Search for "Mikroskooppi" (Finnish)
        mock_should_translate.return_value = True

        # Mock translation+embedding response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'translated_text': 'Microscope',
            'embedding_en': [1.0] + [0.0] * 767
        }
        mock_post.return_value = mock_response

        url = '/api/instruments/search/?q=Mikroskooppi'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.inst1.id)

        # Verify calls
        mock_post.assert_called_with(
            "http://semantic-search-service:8001/process",
            json={"text": "Mikroskooppi"},
            timeout=5.0
        )

    @patch('instrument_registry.views.requests.post')
    def test_search_service_down(self, mock_post):
        """Test that search returns 500 when the external service is unreachable"""
        mock_post.side_effect = requests.exceptions.RequestException("Down")

        url = '/api/instruments/search/?q=test'
        response = self.client.get(url)

        # Expecting 500 as per code in views.py
        self.assertEqual(response.status_code, 500)

    def test_search_no_query(self):
        """Test that searching without a query parameter returns 400"""
        url = '/api/instruments/search/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
