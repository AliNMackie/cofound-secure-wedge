import time
import uuid
import structlog
from typing import Dict
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from src.schemas.requests import ProposalRequest
from src.schemas.responses import ProposalResponse
from src.services.content import ContentGenerator
from src.services.pdf_factory import render_pdf
from src.services.word_factory import render_docx
from src.services.storage import storage_service
from src.core.config import settings

router = APIRouter()
logger = structlog.get_logger()

# Initialize content generator
content_generator = ContentGenerator()

@router.post("/generate/proposal", response_model=Dict[str, str])
async def generate_proposal(request: ProposalRequest):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    log = logger.bind(request_id=request_id, client_id=request.client_id)
    log.info("Received proposal generation request")

    try:
        # 1. Generate Content
        prompt = f"Create a proposal for {request.client_id} with scope: {', '.join(request.project_scope)}. Financials: {request.financial_data}"
        log.info("Generating content...")
        section_content = content_generator.generate_section(prompt, request.domain_profile)
        
        # Prepare data for template
        template_data = section_content.model_dump()
        template_data["client_id"] = request.client_id
        
        # 2. Render Document
        filename = f"proposal_{request.client_id}_{request_id}"
        file_bytes = None
        content_type = ""
        
        if request.output_format == "pdf":
            filename += ".pdf"
            content_type = "application/pdf"
            # Using a default template for now
            file_bytes = await render_pdf(template_data, "default_proposal.html")
            
        elif request.output_format == "docx":
            filename += ".docx"
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            # Using a default template for now
            file_bytes = render_docx(template_data, "default_proposal.docx")
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported output format")

        # 3. Upload and Sign
        log.info("Uploading to storage...")
        signed_url = storage_service.upload_and_sign(file_bytes, filename, content_type)
        
        # Calculate latency
        latency = time.time() - start_time
        log.info("Request processed successfully", latency=latency)
        
        return {
            "status": "success", 
            "url": signed_url
        }

    except Exception as e:
        log.error("Request failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
