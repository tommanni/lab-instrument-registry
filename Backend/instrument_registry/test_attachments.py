from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from .models import Instrument, InstrumentAttachment
from .serializers import RegistryUserSerializer
import json
import tempfile
import os
import shutil

User = get_user_model()

# Create a temporary directory for all test media files
TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class TestAttachmentAPIWithoutAuth(TestCase):
    """Test attachment API endpoints without authentication"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Clean up test media directory
        if os.path.exists(TEST_MEDIA_ROOT):
            shutil.rmtree(TEST_MEDIA_ROOT)
        # Recreate it for next test class
        os.makedirs(TEST_MEDIA_ROOT, exist_ok=True)

    @classmethod
    def setUpTestData(cls):
        # Create a test instrument
        cls.instrument = Instrument.objects.create(
            tuotenimi="Test Instrument",
            merkki_ja_malli="Test Manufacturer Test Model",
            sarjanumero="TEST123",
            yksikko="Test Unit",
            kampus="Test Campus",
            rakennus="Test Building",
            huone="Test Room",
            vastuuhenkilo="Test Person",
            tilanne="Käytössä"
        )

    def test_list_attachments_requires_auth(self):
        """Test that listing attachments requires authentication"""
        response = self.client.get(f"/api/instruments/{self.instrument.id}/attachments/")
        self.assertEqual(response.status_code, 401)

    def test_create_attachment_requires_auth(self):
        """Test that creating attachments requires authentication"""
        test_file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
        response = self.client.post(
            f"/api/instruments/{self.instrument.id}/attachments/",
            {"file": test_file, "description": "Test"},
            format="multipart"
        )
        self.assertEqual(response.status_code, 401)




@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class TestAttachmentAPIWithAuth(TestCase):
    """Test attachment API endpoints with authentication"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Clean up test media directory
        if os.path.exists(TEST_MEDIA_ROOT):
            shutil.rmtree(TEST_MEDIA_ROOT)
        # Recreate it for next test class
        os.makedirs(TEST_MEDIA_ROOT, exist_ok=True)

    @classmethod
    def setUpTestData(cls):
        # Create a test user
        serializer = RegistryUserSerializer(data={
            "email": "test@test.com",
            "full_name": "Test User",
            "password": "testpass123"
        })
        serializer.is_valid()
        cls.user = serializer.save()

        # Create a test instrument
        cls.instrument = Instrument.objects.create(
            tuotenimi="Test Instrument",
            merkki_ja_malli="Test Manufacturer Test Model",
            sarjanumero="TEST123",
            yksikko="Test Unit",
            kampus="Test Campus",
            rakennus="Test Building",
            huone="Test Room",
            vastuuhenkilo="Test Person",
            tilanne="Käytössä"
        )

    def setUp(self):
        # Log in before each test
        self.client.post("/api/login/", {
            "email": "test@test.com",
            "password": "testpass123"
        })

    def test_list_attachments_empty(self):
        """Test listing attachments when there are none"""
        response = self.client.get(f"/api/instruments/{self.instrument.id}/attachments/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_create_attachment(self):
        """Test creating an attachment via API"""
        test_file = SimpleUploadedFile("test.pdf", b"test content", content_type="application/pdf")
        response = self.client.post(
            f"/api/instruments/{self.instrument.id}/attachments/",
            {"file": test_file, "description": "Test attachment"},
            format="multipart"
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["description"], "Test attachment")
        self.assertTrue(data["file"].endswith(".pdf"))

    def test_create_attachment_with_empty_description(self):
        """Test that empty description is allowed (blank=True in model)"""
        test_file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
        response = self.client.post(
            f"/api/instruments/{self.instrument.id}/attachments/",
            {"file": test_file, "description": ""},
            format="multipart"
        )

        # Should succeed since description is blank=True
        self.assertEqual(response.status_code, 201)

    def test_list_attachments_with_data(self):
        """Test listing attachments when they exist"""
        # Create via API to ensure all fields are set correctly
        test_file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
        self.client.post(
            f"/api/instruments/{self.instrument.id}/attachments/",
            {"file": test_file, "description": "Test 1"},
            format="multipart"
        )

        response = self.client.get(f"/api/instruments/{self.instrument.id}/attachments/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["description"], "Test 1")

    def test_delete_attachment(self):
        """Test deleting an attachment via API"""
        # Create via API first
        test_file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
        create_response = self.client.post(
            f"/api/instruments/{self.instrument.id}/attachments/",
            {"file": test_file, "description": "Test"},
            format="multipart"
        )
        attachment_id = create_response.json()["id"]

        response = self.client.delete(f"/api/attachments/{attachment_id}/")
        self.assertEqual(response.status_code, 204)

        # Verify it's deleted
        self.assertFalse(InstrumentAttachment.objects.filter(id=attachment_id).exists())

    def test_download_attachment(self):
        """Test downloading an attachment"""
        test_content = b"test file content"
        test_file = SimpleUploadedFile("test.pdf", test_content, content_type="application/pdf")
        create_response = self.client.post(
            f"/api/instruments/{self.instrument.id}/attachments/",
            {"file": test_file, "description": "Test"},
            format="multipart"
        )
        attachment_id = create_response.json()["id"]

        response = self.client.get(f"/api/attachments/{attachment_id}/download/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])
        # FileResponse uses streaming_content, so we need to read it
        content = b"".join(response.streaming_content)
        self.assertEqual(content, test_content)

    def test_attachment_history_tracking(self):
        """Test that attachment changes are tracked in history"""
        test_file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
        response = self.client.post(
            f"/api/instruments/{self.instrument.id}/attachments/",
            {"file": test_file, "description": "Original description"},
            format="multipart"
        )

        attachment_id = response.json()["id"]
        attachment = InstrumentAttachment.objects.get(id=attachment_id)

        # Check history was created
        self.assertEqual(attachment.history.count(), 1)

        # Update description
        attachment.description = "Updated description"
        attachment.save()

        # Check history was updated
        self.assertEqual(attachment.history.count(), 2)
        latest_history = attachment.history.first()
        self.assertEqual(latest_history.description, "Updated description")

    def test_disk_space_check(self):
        """Test that disk space is checked before upload"""
        from unittest.mock import patch

        # Mock disk_usage to simulate 95% full disk
        mock_usage = type('obj', (object,), {
            'total': 100 * 1024 * 1024 * 1024,  # 100GB
            'used': 95 * 1024 * 1024 * 1024,     # 95GB (95% full)
            'free': 5 * 1024 * 1024 * 1024       # 5GB
        })

        with patch('shutil.disk_usage', return_value=mock_usage):
            test_file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
            response = self.client.post(
                f"/api/instruments/{self.instrument.id}/attachments/",
                {"file": test_file, "description": "Test"},
                format="multipart"
            )

            # Should return 507 Insufficient Storage
            self.assertEqual(response.status_code, 507)
            self.assertIn('storage', response.json()['detail'].lower())

