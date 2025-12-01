import asyncio
import structlog
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Optional

logger = structlog.get_logger()

def render_pdf_sync(html_content: str) -> bytes:
    """
    Synchronous function to render PDF from HTML content using WeasyPrint.
    """
    return HTML(string=html_content).write_pdf()

async def render_pdf(data: dict, template_name: str, template_dir: str = "src/templates") -> bytes:
    """
    Renders a PDF from a Jinja2 template and data.
    Uses asyncio.to_thread to avoid blocking the event loop during PDF generation.
    """
    try:
        logger.info("Rendering PDF", template=template_name)
        
        # Setup Jinja2 environment
        # Note: In a real app, we might want to cache the environment
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)
        
        # Render HTML
        html_content = template.render(**data)
        
        # Generate PDF in a separate thread
        pdf_bytes = await asyncio.to_thread(render_pdf_sync, html_content)
        
        return pdf_bytes
    except Exception as e:
        logger.error("PDF generation failed", error=str(e))
        raise e
