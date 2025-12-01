import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from apps.api.main import app

class TestAPIStatus(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("apps.api.main.FirestoreClient")
    def test_get_job_status_success(self, MockFirestore):
        # Setup mock
        mock_firestore_instance = MagicMock()
        MockFirestore.return_value = mock_firestore_instance
        
        # Mock the global firestore_client used in the endpoint
        with patch("apps.api.main.firestore_client", mock_firestore_instance):
            mock_doc_ref = MagicMock()
            mock_firestore_instance.client.collection.return_value.document.return_value = mock_doc_ref
            
            mock_doc = MagicMock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {
                "tenant_id": "tenant-abc",
                "status": "PROCESSING",
                "job_id": "job-123"
            }
            mock_doc_ref.get.return_value = mock_doc
            
            headers = {"Authorization": "Bearer tenant-abc"}
            response = self.client.get("/job/job-123", headers=headers)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "PROCESSING")

    @patch("apps.api.main.FirestoreClient")
    def test_get_job_status_not_found(self, MockFirestore):
        mock_firestore_instance = MagicMock()
        
        with patch("apps.api.main.firestore_client", mock_firestore_instance):
            mock_doc = MagicMock()
            mock_doc.exists = False
            mock_firestore_instance.client.collection.return_value.document.return_value.get.return_value = mock_doc
            
            headers = {"Authorization": "Bearer tenant-abc"}
            response = self.client.get("/job/job-999", headers=headers)
            
            self.assertEqual(response.status_code, 404)

    @patch("apps.api.main.FirestoreClient")
    def test_get_job_status_unauthorized(self, MockFirestore):
        mock_firestore_instance = MagicMock()
        
        with patch("apps.api.main.firestore_client", mock_firestore_instance):
            mock_doc = MagicMock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {
                "tenant_id": "tenant-xyz", # Different tenant
                "status": "PROCESSING"
            }
            mock_firestore_instance.client.collection.return_value.document.return_value.get.return_value = mock_doc
            
            headers = {"Authorization": "Bearer tenant-abc"}
            response = self.client.get("/job/job-123", headers=headers)
            
            self.assertEqual(response.status_code, 403)

if __name__ == "__main__":
    unittest.main()
