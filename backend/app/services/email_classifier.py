import asyncio
import time
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

try:
    import torch
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    torch = None
    pipeline = None
    AutoTokenizer = None
    AutoModelForSequenceClassification = None
    TRANSFORMERS_AVAILABLE = False
from loguru import logger

from ..config import settings
from ..models.email_models import (
    EmailCategory, 
    EmailClassificationRequest, 
    EmailClassificationResponse,
    EmailProcessingMetrics
)
from ..utils.nlp_processor import NLPProcessor
from .openai_service import openai_service


class EmailClassifier:
    def __init__(self):
        """Initialize the email classifier with AI models and processors."""
        self.nlp_processor = NLPProcessor()
        self.sentiment_classifier = None
        self.tokenizer = None
        self.model = None
        self.is_model_loaded = False
        self.metrics = EmailProcessingMetrics()
        
        # Classification keywords for rule-based fallback
        self.productive_keywords = {
            'portuguese': [
                'problema', 'erro', 'ajuda', 'suporte', 'dúvida', 'questão',
                'solicitação', 'pedido', 'requisição', 'atualização', 'status',
                'informação', 'documento', 'arquivo', 'prazo', 'urgente',
                'reunião', 'meeting', 'projeto', 'tarefa', 'deadline',
                'aprovação', 'autorização', 'confirmação', 'verificação',
                'relatório', 'dados', 'análise', 'proposta', 'orçamento'
            ],
            'english': [
                'problem', 'issue', 'error', 'help', 'support', 'question',
                'request', 'update', 'status', 'information', 'document',
                'file', 'deadline', 'urgent', 'meeting', 'project', 'task',
                'approval', 'authorization', 'confirmation', 'verification',
                'report', 'data', 'analysis', 'proposal', 'quote', 'budget'
            ]
        }
        
        self.unproductive_keywords = {
            'portuguese': [
                'parabéns', 'felicitações', 'aniversário', 'natal', 'ano novo',
                'obrigado', 'agradeço', 'agradecimento', 'bom dia', 'boa tarde',
                'boa noite', 'feliz', 'sucesso', 'tudo bem', 'cumprimento',
                'saudação', 'abraço', 'beijo', 'férias', 'feriado'
            ],
            'english': [
                'congratulations', 'happy', 'birthday', 'christmas', 'new year',
                'thanks', 'thank you', 'good morning', 'good afternoon',
                'good evening', 'best wishes', 'success', 'vacation', 'holiday',
                'greeting', 'celebration', 'party'
            ]
        }
    
    async def initialize_model(self) -> None:
        """Initialize the AI model for sentiment analysis."""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available, using rule-based classification only")
            self.is_model_loaded = False
            return
            
        try:
            logger.info("Initializing AI model for email classification...")
            
            model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=settings.MODEL_CACHE_DIR
            )
            
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                cache_dir=settings.MODEL_CACHE_DIR
            )
            
            # Create pipeline
            self.sentiment_classifier = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                return_all_scores=True,
                device=0 if torch.cuda.is_available() else -1
            )
            
            self.is_model_loaded = True
            logger.info("AI model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI model: {str(e)}")
            logger.warning("Falling back to rule-based classification")
            self.is_model_loaded = False
    
    def _classify_with_rules(self, text: str, features: Dict[str, Any]) -> Tuple[EmailCategory, float]:
        text_lower = text.lower()
        language = features.get('language', 'portuguese')
        
        # Count productive indicators
        productive_score = 0
        productive_found = []
        for keyword in self.productive_keywords.get(language, []):
            if keyword in text_lower:
                productive_score += 2  # Aumentar peso das palavras produtivas
                productive_found.append(keyword)

        # Count unproductive indicators
        unproductive_score = 0
        unproductive_found = []
        for keyword in self.unproductive_keywords.get(language, []):
            if keyword in text_lower:
                unproductive_score += 3  # Aumentar ainda mais o peso das palavras improdutivas
                unproductive_found.append(keyword)

        
        # Additional scoring based on features
        if features.get('question_score', 0) > 0:
            productive_score += 2
        
        if features.get('urgency_score', 0) > 0:
            productive_score += 3
        
        if features.get('greeting_score', 0) > 2:  # Lots of greetings might be unproductive
            unproductive_score += 1
        
        if features.get('word_count', 0) < 20:  # Very short emails might be unproductive
            unproductive_score += 1
        
        # Determine category and confidence
        total_score = productive_score + unproductive_score

        if total_score == 0:
            return EmailCategory.PRODUCTIVE, 0.55

        # Calcular confiança mais dinâmica baseada no conteúdo
        score_difference = abs(productive_score - unproductive_score)
        base_confidence = 0.65

        if productive_score > unproductive_score:
            # Quanto maior a diferença, maior a confiança
            confidence = min(0.95, base_confidence + (score_difference / max(total_score, 1)) * 0.25)
            # Bonus para palavras muito específicas
            if productive_score >= 6:  # Múltiplas palavras produtivas
                confidence = min(0.98, confidence + 0.1)
            return EmailCategory.PRODUCTIVE, confidence
        elif unproductive_score > productive_score:
            confidence = min(0.95, base_confidence + (score_difference / max(total_score, 1)) * 0.25)
            # Bonus para palavras muito específicas
            if unproductive_score >= 9:  # Múltiplas palavras improdutivas
                confidence = min(0.98, confidence + 0.1)
            return EmailCategory.UNPRODUCTIVE, confidence
        else:
            # Empate - baixa confiança
            return EmailCategory.PRODUCTIVE, 0.52
    
    async def _classify_with_ai(self, text: str) -> Tuple[EmailCategory, float]:
        try:
            # Truncate text if too long
            if len(text) > 500:
                text = text[:500]

            # Get sentiment scores
            results = self.sentiment_classifier(text)

            if not results or not isinstance(results, list) or not results[0]:
                raise Exception("Invalid AI model response")

            scores = results[0]

            # Find the highest confidence score
            best_result = max(scores, key=lambda x: x['score'])
            sentiment = best_result['label'].lower()
            confidence = best_result['score']


            # Lógica melhorada: usar palavras-chave em combinação com sentiment
            text_lower = text.lower()

            # Detectar palavras-chave improdutivas diretamente
            unproductive_keywords = [
                'parabéns', 'felicitações', 'aniversário', 'natal', 'obrigado', 'agradeço',
                'bom dia', 'boa tarde', 'boa noite', 'feliz', 'abraço', 'beijo', 'tudo bem',
                'oi pessoal', 'olá', 'como vai', 'como está', 'cumprimentos', 'saudações',
                'fim de semana', 'feriado', 'férias', 'festa', 'celebração', 'comemoração'
            ]
            productive_keywords = [
                'problema', 'erro', 'ajuda', 'urgente', 'prazo', 'relatório', 'dados', 'projeto',
                'reunião', 'reuniao', 'meeting', 'solicitação', 'pedido', 'informação', 'documento', 'arquivo',
                'cancelada', 'cancelado', 'adiada', 'adiado', 'remarcada', 'remarcado'
            ]

            unproductive_count = sum(1 for kw in unproductive_keywords if kw in text_lower)
            productive_count = sum(1 for kw in productive_keywords if kw in text_lower)

            # Priorizar palavras-chave sobre sentiment
            if unproductive_count > 0:
                # Se tem palavras improdutivas, é improdutivo
                return EmailCategory.UNPRODUCTIVE, min(0.9, confidence + 0.15)
            elif productive_count > 0:
                # Se tem palavras produtivas, é produtivo
                return EmailCategory.PRODUCTIVE, min(0.9, confidence + 0.1)
            elif sentiment in ['positive', 'pos']:
                # Positivo sem palavras específicas = mais provável ser improdutivo
                return EmailCategory.UNPRODUCTIVE, min(0.75, confidence)
            elif sentiment in ['negative', 'neg']:
                # Negativo geralmente indica problemas = produtivo
                return EmailCategory.PRODUCTIVE, min(0.8, confidence)
            else:
                # Neutral - default produtivo com baixa confiança
                return EmailCategory.PRODUCTIVE, min(0.55, confidence)

        except Exception as e:
            logger.error(f"AI classification failed: {str(e)}")
            return EmailCategory.PRODUCTIVE, 0.5
    
    def _generate_response(self, category: EmailCategory, features: Dict[str, Any]) -> str:
        if category == EmailCategory.PRODUCTIVE:
            responses = settings.PRODUCTIVE_RESPONSES
        else:
            responses = settings.UNPRODUCTIVE_RESPONSES
        
        if features.get('urgency_score', 0) > 0 and category == EmailCategory.PRODUCTIVE:
            urgent_responses = [r for r in responses if 'breve' in r or 'hoje' in r or 'rápid' in r]
            if urgent_responses:
                return random.choice(urgent_responses)
        
        return random.choice(responses)
    
    def _update_metrics(self, category: EmailCategory, processing_time: float, confidence: float) -> None:
        self.metrics.total_processed += 1
        
        if category == EmailCategory.PRODUCTIVE:
            self.metrics.productive_count += 1
        else:
            self.metrics.unproductive_count += 1
        
        total = self.metrics.total_processed
        self.metrics.average_confidence = (
            (self.metrics.average_confidence * (total - 1) + confidence) / total
        )
        self.metrics.average_processing_time = (
            (self.metrics.average_processing_time * (total - 1) + processing_time) / total
        )
        self.metrics.last_updated = datetime.now(timezone.utc)
    
    async def classify_email(self, request: EmailClassificationRequest) -> EmailClassificationResponse:

        start_time = time.time()
        
        try:
            logger.info(f"Starting email classification for content length: {len(request.content)}")

            # Check user preference for AI model
            force_openai = False
            force_local = False
            if request.metadata:
                force_openai = request.metadata.get('use_openai', False)
                force_local = request.metadata.get('preferred_model') == 'local'

            # Try OpenAI classification first if available and preferred
            category = EmailCategory.PRODUCTIVE
            confidence = 0.6
            classification_method = "rule-based"
            suggested_response = ""

            if openai_service.is_available() and force_openai and not force_local:
                try:
                    openai_result = await openai_service.classify_email(request.content)
                    if openai_result:
                        category = EmailCategory.PRODUCTIVE if openai_result.get('categoria', '').lower() == 'produtivo' else EmailCategory.UNPRODUCTIVE
                        confidence = float(openai_result.get('confianca', 0.8))
                        classification_method = "openai"

                        # Generate response using OpenAI
                        suggested_response = await openai_service.generate_response(request.content, category.value) or ""

                        logger.info(f"OpenAI classification: {category.value} ({confidence:.2f})")

                        # Skip other methods if OpenAI was successful
                        processing_time = time.time() - start_time
                        self._update_metrics(category, processing_time, confidence)

                        return EmailClassificationResponse(
                            category=category.value,
                            confidence=confidence,
                            suggested_response=suggested_response,
                            processing_time=processing_time,
                            timestamp=datetime.now(timezone.utc),
                            model_used=classification_method
                        )
                except Exception as e:
                    logger.warning(f"OpenAI classification failed, falling back to local methods: {e}")

            # Skip local models if OpenAI was forced and failed
            if force_openai and not openai_service.is_available():
                raise Exception("OpenAI was requested but is not available. Check API key configuration.")

            # Preprocess the text for local classification
            cleaned_text = self.nlp_processor.clean_text(request.content)

            if not cleaned_text:
                raise ValueError("No meaningful content found after preprocessing")
            
            # Extract features
            features = self.nlp_processor.extract_key_features(cleaned_text)

            if self.is_model_loaded and self.sentiment_classifier:
                preprocessed_text = self.nlp_processor.preprocess_for_classification(
                    cleaned_text, remove_stopwords=True, apply_stemming=False
                )
                category, confidence = await self._classify_with_ai(preprocessed_text)
                logger.info(f"AI classification: {category.value} (confidence: {confidence:.3f})")
            else:
                logger.info("Using rule-based classification")
                category, confidence = self._classify_with_rules(cleaned_text, features)
                logger.info(f"Rule-based classification: {category.value} (confidence: {confidence:.3f})")
            
            # Generate response
            suggested_response = self._generate_response(category, features)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(category, processing_time, confidence)
            
            response = EmailClassificationResponse(
                category=category.value,
                confidence=confidence,
                suggested_response=suggested_response,
                processing_time=processing_time,
                timestamp=datetime.now(timezone.utc),
                model_used=classification_method
            )
            
            logger.info(f"Email classified successfully in {processing_time:.3f}s: {category.value}")
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Email classification failed after {processing_time:.3f}s: {str(e)}")
            raise Exception(f"Classification failed: {str(e)}")
    
    async def classify_multiple_emails(self, requests: List[EmailClassificationRequest]) -> List[EmailClassificationResponse]:
        """
        Classify multiple emails concurrently.
        
        Args:
            requests: List of email classification requests
            
        Returns:
            List of classification responses
        """
        logger.info(f"Starting batch classification for {len(requests)} emails")
        
        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
        
        async def classify_with_semaphore(request):
            async with semaphore:
                return await self.classify_email(request)
        
        tasks = [classify_with_semaphore(request) for request in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to classify email {i}: {str(result)}")
                # Create error response
                responses.append(EmailClassificationResponse(
                    category=EmailCategory.PRODUCTIVE.value,  # Default
                    confidence=0.0,
                    suggested_response="Desculpe, não foi possível processar este email no momento.",
                    processing_time=0.0,
                    timestamp=datetime.now(timezone.utc),
                    model_used="error_fallback"
                ))
            else:
                responses.append(result)
        
        logger.info(f"Batch classification completed: {len(responses)} results")
        return responses
    
    def get_metrics(self) -> EmailProcessingMetrics:
        """Get current processing metrics."""
        return self.metrics
    
    def reset_metrics(self) -> None:
        """Reset processing metrics."""
        self.metrics = EmailProcessingMetrics()
        logger.info("Processing metrics reset")


# Global classifier instance
email_classifier = EmailClassifier()