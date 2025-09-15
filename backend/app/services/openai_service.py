"""
OpenAI Service for enhanced email classification and response generation.
"""

import asyncio
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from loguru import logger

from ..config import settings


class OpenAIService:
    """Service for integrating OpenAI API capabilities."""

    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize OpenAI client if API key is provided."""
        if settings.OPENAI_API_KEY and settings.USE_OPENAI:
            try:
                self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.info("OpenAI integration disabled - no API key provided or USE_OPENAI=False")

    async def classify_email(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Classify email content using OpenAI.

        Args:
            content: Email content to classify

        Returns:
            Classification result or None if OpenAI is not available
        """
        if not self.client:
            return None

        try:
            prompt = f"""
Analise o seguinte email e classifique como PRODUTIVO ou IMPRODUTIVO.

PRODUTIVO: Emails relacionados a trabalho, negócios, solicitações importantes, urgências, problemas técnicos, reuniões, projetos, vendas, suporte, etc.

IMPRODUTIVO: Emails pessoais, saudações casuais, spam, promoções não solicitadas, correntes, piadas, conversas informais, etc.

Email para análise:
"{content}"

Responda apenas em formato JSON:
{{
    "categoria": "produtivo" ou "improdutivo",
    "confianca": 0.0-1.0,
    "motivo": "breve explicação da classificação"
}}
"""

            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um especialista em classificação de emails. Sempre responda em JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            import json
            try:
                result = json.loads(result_text)
                logger.info(f"OpenAI classification: {result.get('categoria')} ({result.get('confianca')})")
                return result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse OpenAI response as JSON: {result_text}")
                return None

        except Exception as e:
            logger.error(f"OpenAI classification failed: {e}")
            return None

    async def generate_response(self, email_content: str, category: str) -> Optional[str]:
        """
        Generate appropriate response using OpenAI.

        Args:
            email_content: Original email content
            category: Email category (produtivo/improdutivo)

        Returns:
            Generated response or None if OpenAI is not available
        """
        if not self.client:
            return None

        try:
            if category.lower() == "produtivo":
                prompt = f"""
Gere uma resposta profissional e apropriada para este email de trabalho:

"{email_content}"

A resposta deve ser:
- Profissional e cortês
- Reconhecer a solicitação/problema
- Indicar próximos passos quando apropriado
- Máximo 3-4 linhas
- Em português brasileiro
"""
            else:
                prompt = f"""
Gere uma resposta amigável e educada para este email pessoal/informal:

"{email_content}"

A resposta deve ser:
- Amigável e calorosa
- Agradecer a mensagem
- Reciprocar sentimentos quando apropriado
- Máximo 2-3 linhas
- Em português brasileiro
"""

            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um assistente que gera respostas profissionais para emails. Seja conciso e apropriado."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE
            )

            generated_response = response.choices[0].message.content.strip()
            logger.info("OpenAI response generated successfully")
            return generated_response

        except Exception as e:
            logger.error(f"OpenAI response generation failed: {e}")
            return None

    def is_available(self) -> bool:
        """Check if OpenAI service is available."""
        return self.client is not None and settings.USE_OPENAI


# Global instance
openai_service = OpenAIService()