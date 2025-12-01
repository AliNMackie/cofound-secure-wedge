import unittest
from unittest.mock import MagicMock, patch
from apps.worker.processor import ContractProcessor

class TestContractProcessor(unittest.TestCase):
    @patch("apps.worker.processor.dlp_v2.DlpServiceClient")
    @patch("apps.worker.processor.storage.Client")
    @patch("apps.worker.processor.FirestoreClient")
    @patch("apps.worker.processor.vertexai.init")
    @patch("apps.worker.processor.GenerativeModel")
    def setUp(self, MockModel, MockVertex, MockFirestore, MockStorage, MockDLP):
        self.processor = ContractProcessor()
        # MockModel is called twice now (primary and shadow)
        self.mock_model_primary = MagicMock()
        self.mock_model_shadow = MagicMock()
        MockModel.side_effect = [self.mock_model_primary, self.mock_model_shadow]
        
        # Re-init processor to catch side_effect
        self.processor = ContractProcessor()
        
        self.mock_firestore = MockFirestore.return_value
        self.mock_storage = MockStorage.return_value
        self.mock_dlp = MockDLP.return_value

    def test_sanitize_document(self):
        mock_response = MagicMock()
        mock_response.result.findings = []
        self.mock_dlp.inspect_content.return_value = mock_response
        
        result, _ = self.processor.sanitize_document("Text")
        self.assertEqual(result, "Text")

    def test_analyze_contract_shadow_mode(self):
        # Setup mock responses
        primary_response = MagicMock()
        primary_response.text = '```json\n[{"original_text": "Clause 1", "status": "FLAGGED"}]\n```'
        self.processor.model.generate_content.return_value = primary_response
        
        shadow_response = MagicMock()
        shadow_response.text = '```json\n[{"original_text": "Clause 1", "status": "PASS"}]\n```'
        self.processor.shadow_model.generate_content.return_value = shadow_response
        
        # We need to capture stdout to verify the log, but simpler to just verify logic flows
        # and doesn't crash.
        
        result = self.processor.analyze_contract("Sanitized Text", "job-123")
        
        # Verify primary result is returned
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "FLAGGED")
        
        # Verify both models called
        self.processor.model.generate_content.assert_called()
        self.processor.shadow_model.generate_content.assert_called()

    def test_analyze_contract_shadow_failure(self):
        # Primary succeeds, Shadow fails
        primary_response = MagicMock()
        primary_response.text = '```json\n[]\n```'
        self.processor.model.generate_content.return_value = primary_response
        
        self.processor.shadow_model.generate_content.side_effect = Exception("Shadow Broken")
        
        result = self.processor.analyze_contract("Sanitized Text", "job-123")
        
        # Should still return primary result
        self.assertEqual(len(result), 0)
        
    def test_analyze_contract_primary_failure(self):
        # Primary fails
        self.processor.model.generate_content.side_effect = Exception("Primary Broken")
        
        result = self.processor.analyze_contract("Sanitized Text", "job-123")
        
        # Should return error stub
        self.assertEqual(result[0]["status"], "FLAGGED")
        self.assertIn("Error analyzing", result[0]["original_text"])

if __name__ == "__main__":
    unittest.main()
