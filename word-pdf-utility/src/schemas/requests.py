from typing import Literal, List, Dict
from pydantic import BaseModel

class ProposalRequest(BaseModel):
    client_id: str
    domain_profile: Literal['consulting', 'tech', 'finance']
    project_scope: List[str]
    financial_data: Dict[str, str]
    template_version: str = "v1"
    output_format: Literal['pdf', 'docx'] = "pdf"
