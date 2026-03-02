"""
Pleading builder for assembling and generating court filings.
Orchestrates AI body generation and delegates to PleadingGenerator for formatting.
"""

import uuid
import os
import re
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .pleading_generator import get_pleading_generator

logger = logging.getLogger(__name__)


class PleadingBuilder:
    """Builds court pleading documents with optional AI body generation."""

    def __init__(self, output_dir: str = "./data/uploads/generated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pleading_generator = get_pleading_generator()

    async def generate_pleading(
        self,
        user_id: str,
        case_data: Dict[str, Any],
        attorney_info: Dict[str, str],
        document_title: str,
        body_paragraphs: Optional[List[str]],
        representing_party: str,
        attorney_capacity: str = "By his Attorney,",
        include_certification: bool = True,
        certification_date: Optional[str] = None,
        service_list: Optional[List[str]] = None,
        ai_generate_body: bool = False,
        ai_prompt: Optional[str] = None,
        body_text: Optional[str] = None,
        filing_method: str = "ecf",
        service_method: str = "ecf_auto",
    ) -> Dict[str, Any]:
        """Generate a court pleading document."""

        # AI body generation if requested — returns markdown-lite body_text
        if ai_generate_body and ai_prompt:
            body_text = await self._generate_body_with_ai(
                ai_prompt, case_data, document_title
            )
            body_paragraphs = None

        if not body_text and not body_paragraphs:
            raise ValueError("No body content provided or generated")

        # Generate IDs and paths
        pleading_id = f"plead_{uuid.uuid4().hex[:12]}"
        user_output_dir = self.output_dir / user_id
        user_output_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize for filename
        safe_title = re.sub(r'[^a-zA-Z0-9_.\-]', '_', document_title)[:40]
        safe_case = re.sub(r'[^a-zA-Z0-9_.\-]', '_', case_data.get("case_number", ""))[:20]
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"{pleading_id}_{safe_case}_{safe_title}_{date_str}.docx"
        output_path = user_output_dir / filename

        # Generate the document
        self.pleading_generator.generate_pleading(
            output_path=output_path,
            case_data=case_data,
            attorney_info=attorney_info,
            document_title=document_title,
            body_paragraphs=body_paragraphs or [],
            representing_party=representing_party,
            attorney_capacity=attorney_capacity,
            include_certification=include_certification,
            certification_date=certification_date,
            service_list=service_list,
            body_text=body_text,
            filing_method=filing_method,
            service_method=service_method,
        )

        logger.info(f"Generated pleading {pleading_id} for user {user_id}")

        return {
            "document_id": pleading_id,
            "filename": filename,
            "file_path": str(output_path),
            "file_size": output_path.stat().st_size,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _generate_body_with_ai(
        self, prompt: str, case_data: Dict[str, Any], document_title: str
    ) -> str:
        """Generate motion body text using Groq AI. Returns markdown-lite formatted text."""
        try:
            from groq import Groq

            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")

            client = Groq(api_key=api_key)

            plaintiffs = ", ".join(case_data.get("plaintiff_names", []))
            defendants = ", ".join(case_data.get("defendant_names", []))
            case_number = case_data.get("case_number", "")

            system_prompt = f"""You are a legal writing assistant drafting court pleadings.

Case: {plaintiffs} v. {defendants}
Case Number: {case_number}
Document: {document_title}

Write the body text for this court filing based on the user's instructions.
Rules:
- Write in formal legal style appropriate for court
- Use section headings with ## prefix (e.g., ## STATEMENT OF FACTS)
- Use **bold** for emphasis where appropriate
- Use __underline__ for case names (e.g., __Smith v. Jones__)
- Use numbered lists (1. , 2. ) for enumerated arguments
- Use bullet lists (- ) for supporting points
- Do NOT include the caption, title, signature block, or certification
- Only write the body text
- Return ONLY the body text, not wrapped in JSON or code blocks
- Keep paragraphs focused and professional"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Draft the following:\n\n{prompt}"},
                ],
                max_tokens=3000,
                temperature=0.5,
            )

            response_text = response.choices[0].message.content.strip()
            logger.info(f"AI body response: {response_text[:200]}...")

            # Strip code fences if the model wrapped the output
            if response_text.startswith('```'):
                response_text = re.sub(r'^```\w*\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)

            return response_text

        except Exception as e:
            logger.error(f"Error generating body with AI: {e}", exc_info=True)
            raise ValueError(f"AI body generation failed: {str(e)}")


# Singleton
_pleading_builder: Optional[PleadingBuilder] = None


def get_pleading_builder() -> PleadingBuilder:
    """Get or create the singleton PleadingBuilder instance."""
    global _pleading_builder
    if _pleading_builder is None:
        _pleading_builder = PleadingBuilder()
    return _pleading_builder
