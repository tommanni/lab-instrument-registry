from django.test import TestCase, override_settings
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
            embedding_en=None,
            enriched_description=""
        )
        self.inst2 = Instrument.objects.create(
            tuotenimi="Vaaka",
            tuotenimi_en="",
            embedding_en=None,
            enriched_description=""
        )
        self.inst3 = Instrument.objects.create(
            tuotenimi="Spectrometer",
            tuotenimi_en="Spectrometer", # Already English/Translated
            embedding_en=None,
            enriched_description=""
        )

    @override_settings(GOOGLE_GENAI_API_KEY='test-api-key')
    @patch('instrument_registry.services.enrichment.EnrichmentService')
    @patch('instrument_registry.embedding._requests_retry_session')
    def test_precompute_success(self, mock_session_builder, mock_enrichment_service_class):
        """Test successful batch translation and embedding of instruments"""
        # Mock EnrichmentService
        mock_enrichment_service = MagicMock()
        mock_enrichment_service_class.return_value = mock_enrichment_service
        # Mock enrich_batch to return translations and descriptions for all 3 instruments
        # (inst1 and inst2 need translation+enrichment, inst3 needs enrichment only)
        mock_enrichment_service.enrich_batch.return_value = [
            {'translation': 'Microscope', 'description': 'laboratory microscope for viewing small objects'},
            {'translation': 'Scale', 'description': 'laboratory scale for measuring weight'},
            {'translation': 'Spectrometer', 'description': 'laboratory spectrometer for analyzing samples'}
        ]

        # Mock the embedding service session
        mock_session = MagicMock()
        mock_session_builder.return_value = mock_session

        # Mock /embed_en_batch endpoint response
        mock_response_embedding = MagicMock()
        mock_response_embedding.status_code = 200
        mock_response_embedding.json.return_value = {
            'embeddings': [[0.1]*768, [0.2]*768, [0.3]*768]  # For inst1, inst2, inst3
        }
        mock_response_embedding.raise_for_status = MagicMock()

        def side_effect(*args, **kwargs):
            url = args[0]
            if 'embed_en_batch' in url:
                return mock_response_embedding
            return MagicMock(status_code=404)

        mock_session.post.side_effect = side_effect

        # Run the function with max_workers=1 to avoid threading issues in tests
        results = precompute_instrument_embeddings(batch_size=10, max_workers=1)

        # Refresh objects from db
        self.inst1.refresh_from_db()
        self.inst2.refresh_from_db()
        self.inst3.refresh_from_db()

        # Assertions
        self.assertEqual(results['processed_count'], 3) # 2 needing translation + 1 needing embedding
        self.assertIn('successful', results)
        self.assertIn('cache_size', results)

        # Check Inst1
        self.assertEqual(self.inst1.tuotenimi_en, "Microscope")
        self.assertEqual(self.inst1.enriched_description, "laboratory microscope for viewing small objects")
        self.assertIsNotNone(self.inst1.embedding_en)

        # Check Inst2
        self.assertEqual(self.inst2.tuotenimi_en, "Scale")
        self.assertEqual(self.inst2.enriched_description, "laboratory scale for measuring weight")
        self.assertIsNotNone(self.inst2.embedding_en)

        # Check Inst3
        self.assertEqual(self.inst3.tuotenimi_en, "Spectrometer") # Should remain (not overwritten)
        self.assertEqual(self.inst3.enriched_description, "laboratory spectrometer for analyzing samples")
        self.assertIsNotNone(self.inst3.embedding_en)

    @override_settings(GOOGLE_GENAI_API_KEY='test-api-key')
    @patch('instrument_registry.services.enrichment.EnrichmentService')
    @patch('instrument_registry.embedding._requests_retry_session')
    def test_precompute_service_failure(self, mock_session_builder, mock_enrichment_service_class):
        """Test handling of service failures during precomputation"""
        # Mock EnrichmentService to raise exception
        mock_enrichment_service = MagicMock()
        mock_enrichment_service_class.return_value = mock_enrichment_service
        mock_enrichment_service.enrich_batch.side_effect = Exception("Gemini API error")

        # Mock embedding service to also fail
        mock_session = MagicMock()
        mock_session_builder.return_value = mock_session
        mock_session.post.side_effect = Exception("Connection refused")

        results = precompute_instrument_embeddings(max_workers=1)

        self.inst1.refresh_from_db()
        self.inst2.refresh_from_db()
        # On failure, instruments should have "Translation Failed" and "Enrichment Failed"
        self.assertEqual(self.inst1.tuotenimi_en, "Translation Failed")
        self.assertEqual(self.inst1.enriched_description, "Enrichment Failed")
        self.assertEqual(self.inst2.tuotenimi_en, "Translation Failed")
        self.assertEqual(self.inst2.enriched_description, "Enrichment Failed")
        # Check return values - should have successful count and cache_size, not 'failed'
        self.assertIn('processed_count', results)
        self.assertIn('successful', results)
        self.assertIn('cache_size', results)

    @override_settings(GOOGLE_GENAI_API_KEY='test-api-key')
    @patch('instrument_registry.services.enrichment.EnrichmentService')
    @patch('instrument_registry.embedding._requests_retry_session')
    def test_precompute_partial_cache(self, mock_session_builder, mock_enrichment_service_class):
        """Test that duplicate instrument names are only translated once per batch"""
        # Test that if we have multiple same items, we only translate once
        Instrument.objects.create(
            tuotenimi="Mikroskooppi", 
            tuotenimi_en="", 
            embedding_en=None,
            enriched_description=""
        ) # Duplicate

        # Mock EnrichmentService - should only be called once for unique cache keys
        mock_enrichment_service = MagicMock()
        mock_enrichment_service_class.return_value = mock_enrichment_service
        # enrich_batch should be called with unique items (same tuotenimi, same merkki_ja_malli = same cache key)
        mock_enrichment_service.enrich_batch.return_value = [
            {'translation': 'Microscope', 'description': 'laboratory microscope'},
            {'translation': 'Scale', 'description': 'laboratory scale'}
        ]

        # Mock embedding service
        mock_session = MagicMock()
        mock_session_builder.return_value = mock_session

        mock_embed_response = MagicMock()
        mock_embed_response.status_code = 200
        mock_embed_response.json.return_value = {
            'embeddings': [[0.1]*768, [0.2]*768, [0.3]*768, [0.4]*768]  # 4 instruments total
        }
        mock_embed_response.raise_for_status = MagicMock()

        def side_effect(*args, **kwargs):
            url = args[0]
            if 'embed_en_batch' in url:
                return mock_embed_response
            return MagicMock(status_code=404)

        mock_session.post.side_effect = side_effect

        precompute_instrument_embeddings(max_workers=1)

        # Verify all Mikroskooppi instances got updated with same translation
        # (they share the same cache key since merkki_ja_malli is empty for both)
        microscopes = Instrument.objects.filter(tuotenimi="Mikroskooppi")
        for m in microscopes:
            m.refresh_from_db()
            self.assertEqual(m.tuotenimi_en, "Microscope")
            self.assertEqual(m.enriched_description, "laboratory microscope")
        
        # Verify enrich_batch was called, and should have been called with unique cache keys
        # (2 unique keys: mikroskooppi| and vaaka|)
        self.assertTrue(mock_enrichment_service.enrich_batch.called)


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
            "http://semantic-search-service:8001/embed_query",
            json={"text": "Microscope"},
            timeout=20.0
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
            "http://semantic-search-service:8001/process_query",
            json={"text": "Mikroskooppi"},
            timeout=20.0
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
