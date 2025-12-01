import datetime
from typing import Optional, Dict, Any
from uuid import uuid4
from google.cloud import firestore
from shared.models import JobStatus, AuditLog, ContractJob

class FirestoreClient:
    def __init__(self, project_id: Optional[str] = None):
        self.client = firestore.Client(project=project_id)
        self.collection_name = "contract_jobs"

    def create_job(self, tenant_id: str, file_path: str) -> str:
        """
        Creates a new contract job in Firestore.
        
        Args:
            tenant_id: The ID of the tenant.
            file_path: The GCS path of the uploaded file.
            
        Returns:
            The job_id of the created job.
        """
        job_id = str(uuid4())
        
        # Create initial audit log
        initial_audit = AuditLog(
            action="JOB_CREATED",
            details={"file_path": file_path}
        )
        
        # Create ContractJob model instance to validate and get default values
        job = ContractJob(
            job_id=job_id,
            tenant_id=tenant_id,
            file_gcs_path=file_path,
            audit_trail=[initial_audit]
        )
        
        # Convert to dict for Firestore storage, handling datetime serialization if needed
        # model_dump(mode='json') handles datetime conversion to string/isoformat usually,
        # but Firestore client handles native datetime objects.
        # using model_dump() keeps datetimes as objects which is good for firestore.
        job_data = job.model_dump()
        
        doc_ref = self.client.collection(self.collection_name).document(job_id)
        doc_ref.set(job_data)
        
        return job_id

    def update_job_status(self, job_id: str, status: JobStatus, result_data: Optional[Dict[str, Any]] = None):
        """
        Updates the status of a job and appends to the audit trail.
        
        Args:
            job_id: The ID of the job to update.
            status: The new status.
            result_data: Optional dictionary containing analysis results or error details.
        """
        doc_ref = self.client.collection(self.collection_name).document(job_id)
        
        # Create new audit log
        new_audit = AuditLog(
            action=f"STATUS_CHANGED_TO_{status.value}",
            details=result_data
        )
        
        update_data = {
            "status": status.value,
            "audit_trail": firestore.ArrayUnion([new_audit.model_dump()])
        }
        
        if result_data:
            # If there are specific fields in result_data that map to the document structure, 
            # we might want to merge them. For now, assuming result_data might 
            # go into a 'result' field or similar if the model supported it, 
            # or it's just for the audit log.
            # However, looking at VCRReport, maybe we want to store the results separately or 
            # update fields if they exist on ContractJob? 
            # ContractJob doesn't have a 'results' field. 
            # The prompt says "update_job_status(job_id, status, result_data=None)".
            # I will assume result_data is mostly for audit context unless I add a results field.
            # But wait, VCRReport aggregates ContractJob.
            pass

        doc_ref.update(update_data)
