from groq import Groq
import os
from typing import List
import logging
from app.models import SearchResult

logger = logging.getLogger(__name__)


class AnswerSynthesizer:
    """Synthesizes answers from search results using Groq LLM"""

    def __init__(self):
        """Initialize Groq client"""
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not found in environment. Answer synthesis will not work.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
            logger.info("Groq client initialized successfully")

    def synthesize(
        self,
        query: str,
        search_results: List[SearchResult],
        max_tokens: int = 500
    ) -> str:
        """
        Generate a synthesized answer from search results

        Args:
            query: User's question
            search_results: List of SearchResult objects
            max_tokens: Maximum tokens in response

        Returns:
            Synthesized answer as string
        """
        if not self.client:
            return "Error: Groq API key not configured. Please set GROQ_API_KEY environment variable."

        if not search_results:
            return "No relevant information found to answer your question."

        # Build context from search results
        context_parts = []
        for i, result in enumerate(search_results[:5], 1):  # Use top 5 results
            source = f"[Source {i}: {result.metadata.filename}, Page {result.metadata.page}]"
            context_parts.append(f"{source}\n{result.text}\n")

        context = "\n".join(context_parts)

        # Create prompt
        prompt = f"""You are a legal document assistant. Based on the following excerpts from legal documents, provide a clear and concise answer to the user's question.

Context from legal documents:
{context}

User's question: {query}

Instructions:
- Provide a direct answer to the question based ONLY on the information in the context
- Cite sources using [Source X] notation when referencing specific information
- If the context doesn't contain enough information to fully answer, acknowledge this
- Keep your answer concise but complete
- Use professional legal language where appropriate

Answer:"""

        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Latest Llama 3.3 model
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful legal document assistant that provides accurate information based on source documents."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Low temperature for factual responses
                max_tokens=max_tokens,
                top_p=1,
                stream=False
            )

            answer = response.choices[0].message.content
            logger.info(f"Generated answer for query: '{query[:50]}...'")
            return answer

        except Exception as e:
            logger.error(f"Error synthesizing answer: {e}", exc_info=True)
            return f"Error generating answer: {str(e)}"


# Global instance
synthesizer: AnswerSynthesizer = None


def get_synthesizer() -> AnswerSynthesizer:
    """Get the global synthesizer instance"""
    global synthesizer
    if synthesizer is None:
        synthesizer = AnswerSynthesizer()
    return synthesizer
