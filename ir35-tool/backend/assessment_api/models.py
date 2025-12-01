from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class AssessmentRequest(BaseModel):
    engagement_id: str = Field(..., description="Unique identifier for the engagement")
    role_details: str = Field(..., description="Description of the role and responsibilities")
    contract_type: Optional[str] = Field(None, description="Type of contract (e.g., 'Ltd', 'PAYE')")
    answers: Dict[str, Any] = Field(..., description="Key-value pairs of CEST questionnaire answers")

class RagReference(BaseModel):
    id: str
    content_snippet: str
    score: float
    source: Optional[str] = None

class AssessmentResponse(BaseModel):
    assessment_id: str
    status: str
    determination: str
    confidence_score: float
    reasoning: str
    rag_references: List[RagReference]
    timestamp: str
