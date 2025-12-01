import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from apps.api.main import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("apps.api.main.storage.Client")
    @patch("apps.api.main.pubsub_v1.PublisherClient")
    @patch("apps.api.main.FirestoreClient")
    def test_upload_endpoint_success(self, MockFirestore, MockPubSub, MockStorage):
        # Setup mocks
        mock_storage_instance = MagicMock()
        MockStorage.return_value = mock_storage_instance
        mock_bucket = MagicMock()
        mock_storage_instance.bucket.return_value = mock_bucket
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob

        mock_firestore_instance = MagicMock()
        MockFirestore.return_value = mock_firestore_instance
        mock_firestore_instance.create_job.return_value = "job-123"

        mock_pubsub_instance = MagicMock()
        MockPubSub.return_value = mock_pubsub_instance
        
        # We need to repatch the global clients in main because they are initialized at module level
        # A safer way in real apps is using dependency overrides, but since we modify global vars:
        with patch("apps.api.main.storage_client", mock_storage_instance), \
             patch("apps.api.main.firestore_client", mock_firestore_instance), \
             patch("apps.api.main.pubsub_publisher", mock_pubsub_instance):
            
            files = {"file": ("contract.pdf", b"pdf content", "application/pdf")}
            headers = {"Authorization": "Bearer tenant-abc"}
            
            response = self.client.post("/upload", files=files, headers=headers)
            
            self.assertEqual(response.status_code, 202)
            self.assertEqual(response.json(), {"job_id": "job-123"})
            
            # Verify calls
            mock_blob.upload_from_file.assert_called()
            mock_firestore_instance.create_job.assert_called()
            mock_pubsub_instance.publish.assert_called()

    def test_upload_invalid_file_type(self):
        files = {"file": ("image.png", b"png content", "image/png")}
        headers = {"Authorization": "Bearer tenant-abc"}
        response = self.client.post("/upload", files=files, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Only PDF files are allowed", response.json()["detail"])

    def test_missing_auth(self):
        files = {"file": ("contract.pdf", b"pdf content", "application/pdf")}
        response = self.client.post("/upload", files=files)
        self.assertEqual(response.status_code, 401) # Or 422 if FastAPI handles missing header first, but custom dep raises 401

if __name__ == "__main__":
    unittest.main()
