"""
Envelope builder for assembling and generating envelopes.
"""

import uuid
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .envelope_generator import get_envelope_generator

logger = logging.getLogger(__name__)


class EnvelopeBuilder:
    """Builds print-ready envelopes."""

    def __init__(self, output_dir: str = "./uploads/generated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.envelope_generator = get_envelope_generator()

    async def generate_envelope(
        self,
        user_id: str,
        return_address: Dict[str, str],
        recipient_data: Optional[Dict[str, str]] = None,
        ai_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an envelope document.

        Args:
            user_id: User ID from authentication
            return_address: User's return address (from settings)
            recipient_data: Structured recipient address (manual mode)
            ai_prompt: Natural language prompt for AI parsing (AI mode)

        Returns:
            Dict with envelope_id, filename, and file path
        """
        # Parse recipient address with AI if prompt provided
        if ai_prompt:
            logger.info(f"Parsing recipient address from AI prompt: {ai_prompt[:100]}...")
            recipient_data = await self._parse_recipient_address_with_ai(ai_prompt)

        if not recipient_data:
            raise ValueError("No recipient address provided")

        # Generate unique envelope ID
        envelope_id = f"env_{uuid.uuid4().hex[:12]}"

        # Create user output directory
        user_output_dir = self.output_dir / user_id
        user_output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        recipient_name = recipient_data.get('name', 'recipient')
        # Sanitize name for filename
        safe_name = recipient_name.replace(' ', '_').replace('/', '-')[:30]
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"{safe_name}_envelope_{date_str}_{envelope_id}.docx"
        output_path = user_output_dir / filename

        # Generate envelope
        self.envelope_generator.generate_envelope(
            output_path=output_path,
            return_address=return_address,
            recipient_address=recipient_data
        )

        logger.info(f"Generated envelope {envelope_id} for user {user_id}")

        return {
            "envelope_id": envelope_id,
            "filename": filename,
            "file_path": str(output_path),
            "file_size": output_path.stat().st_size,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _parse_recipient_address_with_ai(self, prompt: str) -> Dict[str, str]:
        """
        Parse recipient address from natural language using AI.

        Args:
            prompt: Natural language like "Create envelope to John Smith at 123 Main St, Boston MA 02101"

        Returns:
            Dict with name, line1, line2, city_state_zip
        """
        try:
            from groq import Groq

            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")

            client = Groq(api_key=api_key)

            system_prompt = """You are an address parsing assistant. Extract the recipient's mailing address from the user's request.

Return ONLY valid JSON with these fields:
- name: Recipient's full name
- line1: Street address (number and street name)
- line2: Apartment, suite, unit number (empty string if none)
- city_state_zip: City, State ZIP (e.g., "Boston, MA 02101")

Examples:
Input: "Create envelope to John Smith at 123 Main Street, Boston MA 02101"
Output: {"name": "John Smith", "line1": "123 Main Street", "line2": "", "city_state_zip": "Boston, MA 02101"}

Input: "Mail to Sarah Johnson, 456 Oak Ave Apt 3B, Seattle WA 98101"
Output: {"name": "Sarah Johnson", "line1": "456 Oak Ave", "line2": "Apt 3B", "city_state_zip": "Seattle, WA 98101"}

Return ONLY the JSON, no extra text."""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Parse this address request:\n\n{prompt}"}
                ],
                max_tokens=500,
                temperature=0.2,
            )

            response_text = response.choices[0].message.content.strip()
            logger.info(f"AI response for address parsing: {response_text}")

            # Parse JSON
            import json
            import re

            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = json.loads(response_text)

            # Ensure all expected fields exist
            address = {
                'name': parsed.get('name', ''),
                'line1': parsed.get('line1', ''),
                'line2': parsed.get('line2', ''),
                'city_state_zip': parsed.get('city_state_zip', ''),
            }

            logger.info(f"Parsed address: {address}")
            return address

        except Exception as e:
            logger.error(f"Error parsing address with AI: {e}", exc_info=True)
            # Return empty address as fallback
            return {
                'name': '',
                'line1': '',
                'line2': '',
                'city_state_zip': '',
            }


# Singleton instance
_envelope_builder: Optional[EnvelopeBuilder] = None


def get_envelope_builder() -> EnvelopeBuilder:
    """Get or create the singleton EnvelopeBuilder instance."""
    global _envelope_builder
    if _envelope_builder is None:
        _envelope_builder = EnvelopeBuilder()
    return _envelope_builder
