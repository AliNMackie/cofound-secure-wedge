import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from shared.models import ContractJob, JobStatus, AuditLog, ClauseAnalysis, ClauseStatus, VCRReport
from shared.database import FirestoreClient

class TestModels(unittest.TestCase):
    def test_contract_job_creation(self):
        job = ContractJob(
            tenant_id="tenant-123",
            file_gcs_path="gs://bucket/file.pdf"
        )
        self.assertEqual(job.tenant_id, "tenant-123")
        self.assertEqual(job.status, JobStatus.QUEUED)
        self.assertIsNotNone(job.job_id)
        self.assertIsNotNone(job.upload_timestamp)

    def test_clause_analysis_creation(self):
        clause = ClauseAnalysis(
            original_text="Some legal text",
            risk_score=0.5,
            status=ClauseStatus.PASS,
            ai_reasoning="Looks good"
        )
        self.assertEqual(clause.risk_score, 0.5)
        self.assertEqual(clause.status, ClauseStatus.PASS)

    def test_vcr_report_creation(self):
        job = ContractJob(
            tenant_id="tenant-123",
            file_gcs_path="gs://bucket/file.pdf"
        )
        report = VCRReport(job_details=job)
        self.assertEqual(report.job_details.tenant_id, "tenant-123")

class TestFirestoreClient(unittest.TestCase):
    @patch("shared.database.firestore.Client")
    def test_create_job(self, mock_firestore_client):
        # Setup mock
        mock_client_instance = MagicMock()
        mock_firestore_client.return_value = mock_client_instance
        mock_collection = MagicMock()
        mock_client_instance.collection.return_value = mock_collection
        mock_doc_ref = MagicMock()
        mock_collection.document.return_value = mock_doc_ref

        # Initialize client
        client = FirestoreClient(project_id="test-project")
        
        # Test create_job
        job_id = client.create_job("tenant-123", "gs://bucket/file.pdf")
        
        # Verify interactions
        self.assertTrue(len(job_id) > 0)
        mock_client_instance.collection.assert_called_with("contract_jobs")
        mock_collection.document.assert_called_with(job_id)
        mock_doc_ref.set.assert_called()
        
        # Verify payload structure
        call_args = mock_doc_ref.set.call_args
        payload = call_args[0][0]
        self.assertEqual(payload["tenant_id"], "tenant-123")
        self.assertEqual(payload["file_gcs_path"], "gs://bucket/file.pdf")
        self.assertEqual(payload["status"], "QUEUED")

    @patch("shared.database.firestore.Client")
    def test_update_job_status(self, mock_firestore_client):
        # Setup mock
        mock_client_instance = MagicMock()
        mock_firestore_client.return_value = mock_client_instance
        mock_collection = MagicMock()
        mock_client_instance.collection.return_value = mock_collection
        mock_doc_ref = MagicMock()
        mock_collection.document.return_value = mock_doc_ref

        # Initialize client
        client = FirestoreClient(project_id="test-project")
        
        # Test update_job_status
        client.update_job_status("job-123", JobStatus.PROCESSING, {"info": "started"})
        
        # Verify interactions
        mock_collection.document.assert_called_with("job-123")
        mock_doc_ref.update.assert_called()
        
        # Verify payload
        call_args = mock_doc_ref.update.call_args
        payload = call_args[0][0]
        self.assertEqual(payload["status"], "PROCESSING")
        self.assertIn("audit_trail", payload)

if __name__ == "__main__":
    unittest.main()
