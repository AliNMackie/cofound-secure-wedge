import structlog
from docxtpl import DocxTemplate
from typing import Dict
import io

logger = structlog.get_logger()

def render_docx(data: dict, template_name: str, template_dir: str = "src/templates") -> bytes:
    """
    Renders a DOCX file from a template and data.
    """
    try:
        logger.info("Rendering DOCX", template=template_name)
        
        template_path = f"{template_dir}/{template_name}"
        doc = DocxTemplate(template_path)
        
        doc.render(data)
        
        # Save to memory
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)
        
        return file_stream.getvalue()
    except Exception as e:
        logger.error("DOCX generation failed", error=str(e))
        raise e
