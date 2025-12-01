from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ClauseStatus(str, Enum):
    PASS = "PASS"
    FLAGGED = "FLAGGED"

class AuditLog(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str
    actor: str = "system" # system or user_id
    details: Optional[Dict[str, Any]] = None

class ClauseAnalysis(BaseModel):
    clause_id: str = Field(default_factory=lambda: str(uuid4()))
    original_text: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    status: ClauseStatus
    regulation_violation: Optional[str] = None
    ai_reasoning: str

class ContractJob(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    status: JobStatus = JobStatus.QUEUED
    file_gcs_path: str
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = "gemini-1.5-pro-002"
    audit_trail: List[AuditLog] = Field(default_factory=list)

class VCRReport(BaseModel):
    job_details: ContractJob
    clauses: List[ClauseAnalysis] = Field(default_factory=list)
    human_overrides: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    compliance_score: Optional[float] = None
