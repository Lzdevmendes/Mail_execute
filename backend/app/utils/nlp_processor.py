import re
import string
from typing import List, Set, Dict, Any
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer
from loguru import logger


class NLPProcessor:
    
    def __init__(self):
        self._ensure_nltk_data()
        self.stemmer = PorterStemmer()
        self.portuguese_stopwords = self._get_portuguese_stopwords()
        self.english_stopwords = self._get_english_stopwords()
    
    def _ensure_nltk_data(self) -> None:
        nltk_data_requirements = [
            'punkt',
            'stopwords',
            'rslp' 
        ]
        
        for data_name in nltk_data_requirements:
            try:
                nltk.data.find(f'tokenizers/{data_name}')
            except LookupError:
                try:
                    logger.info(f"Downloading NLTK data: {data_name}")
                    nltk.download(data_name, quiet=True)
                except Exception as e:
                    logger.warning(f"Failed to download NLTK data {data_name}: {str(e)}")
    
    def _get_portuguese_stopwords(self) -> Set[str]:
        try:
            portuguese_stops = set(stopwords.words('portuguese'))
        except:
            portuguese_stops = set()
        
        custom_stops = {
            'att', 'atenciosamente', 'cordialmente', 'abracos', 'abraço',
            'cumprimentos', 'saudacoes', 'obrigado', 'obrigada', 'agradeco',
            'prezado', 'prezada', 'caro', 'cara', 'senhor', 'senhora',
            'sr', 'sra', 'email', 'e-mail', 'assunto', 'ref', 'fwd',
            're', 'encaminho', 'segue', 'anexo', 'anexos'
        }
        
        return portuguese_stops.union(custom_stops)
    
    def _get_english_stopwords(self) -> Set[str]:
        """Get English stopwords with additional custom words."""
        try:
            english_stops = set(stopwords.words('english'))
        except:
            english_stops = set()
        
        custom_stops = {
            'regards', 'sincerely', 'best', 'thanks', 'thank', 'dear',
            'hello', 'hi', 'email', 'subject', 'fwd', 'forward', 're',
            'attachment', 'attached', 'please', 'kind'
        }
        
        return english_stops.union(custom_stops)
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove phone numbers (basic patterns)
        text = re.sub(r'(\+?\d{1,3}[-.\s]?)?\(?\d{2,3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}', '', text)
        
        # Remove excessive whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\!\?\,\;\:\-]', '', text)
        
        # Remove multiple punctuation
        text = re.sub(r'([.!?]){2,}', r'\1', text)
        
        return text.strip()
    
    def tokenize_text(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        try:
            tokens = word_tokenize(text, language='portuguese')
        except:
            tokens = text.split()
        
        tokens = [token for token in tokens if len(token) > 1 and token.isalpha()]
        
        return tokens
    
    def remove_stopwords(self, tokens: List[str], language: str = 'portuguese') -> List[str]:
        if language == 'portuguese':
            stopwords_set = self.portuguese_stopwords
        else:
            stopwords_set = self.english_stopwords
        
        filtered_tokens = [token for token in tokens if token.lower() not in stopwords_set]
        
        return filtered_tokens
    
    def stem_tokens(self, tokens: List[str]) -> List[str]:
        try:
            from nltk.stem import RSLPStemmer
            stemmer = RSLPStemmer()  # Portuguese stemmer
            stemmed = [stemmer.stem(token) for token in tokens]
        except:
            # Fallback to Porter stemmer if RSLP is not available
            stemmed = [self.stemmer.stem(token) for token in tokens]
        
        return stemmed
    
    def extract_sentences(self, text: str) -> List[str]:
        try:
            sentences = sent_tokenize(text, language='portuguese')
        except:
            # Simple fallback sentence extraction
            sentences = text.split('.')
            sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        sentences = self.extract_sentences(text)
        words = self.tokenize_text(text)
        
        stats = {
            'character_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'average_words_per_sentence': len(words) / len(sentences) if sentences else 0,
            'unique_words': len(set(words)),
            'lexical_diversity': len(set(words)) / len(words) if words else 0
        }
        
        return stats
    
    def detect_language(self, text: str) -> str:
        text_lower = text.lower()
        
        # Common Portuguese indicators
        portuguese_indicators = ['que', 'para', 'com', 'uma', 'por', 'são', 'não', 'mais', 'como', 'seu']
        portuguese_score = sum(1 for word in portuguese_indicators if word in text_lower)
        
        # Common English indicators
        english_indicators = ['the', 'and', 'for', 'are', 'with', 'not', 'you', 'this', 'have', 'from']
        english_score = sum(1 for word in english_indicators if word in text_lower)
        
        if portuguese_score > english_score:
            return 'portuguese'
        elif english_score > portuguese_score:
            return 'english'
        else:
            return 'unknown'
    
    def preprocess_for_classification(self, text: str, remove_stopwords: bool = True, 
                                     apply_stemming: bool = False) -> str:
        if not text:
            return ""
        
        # Clean the text
        cleaned_text = self.clean_text(text)
        
        # Tokenize
        tokens = self.tokenize_text(cleaned_text)
        
        # Detect language for appropriate preprocessing
        language = self.detect_language(cleaned_text)
        
        # Remove stopwords if requested
        if remove_stopwords:
            tokens = self.remove_stopwords(tokens, language)
        
        # Apply stemming if requested
        if apply_stemming:
            tokens = self.stem_tokens(tokens)
        
        # Join tokens back into text
        preprocessed_text = ' '.join(tokens)
        
        logger.debug(f"Preprocessed text: {len(text)} -> {len(preprocessed_text)} chars, "
                    f"detected language: {language}")
        
        return preprocessed_text
    
    def extract_key_features(self, text: str) -> Dict[str, Any]:
        # Get basic statistics
        stats = self.get_text_statistics(text)
        
        # Detect urgency indicators
        urgency_words = ['urgente', 'pressa', 'rápido', 'imediato', 'asap', 'emergency', 'urgent']
        urgency_score = sum(1 for word in urgency_words if word in text.lower())
        
        # Detect question indicators
        question_indicators = ['?', 'como', 'quando', 'onde', 'por que', 'what', 'how', 'when', 'where', 'why']
        question_score = sum(1 for indicator in question_indicators if indicator in text.lower())
        
        # Detect greeting patterns
        greeting_words = ['oi', 'olá', 'bom dia', 'boa tarde', 'hello', 'hi', 'dear']
        greeting_score = sum(1 for word in greeting_words if word in text.lower())
        
        # Detect closing patterns
        closing_words = ['obrigado', 'abraço', 'att', 'regards', 'sincerely', 'best']
        closing_score = sum(1 for word in closing_words if word in text.lower())
        
        features = {
            **stats,
            'urgency_score': urgency_score,
            'question_score': question_score,
            'greeting_score': greeting_score,
            'closing_score': closing_score,
            'has_questions': '?' in text,
            'language': self.detect_language(text)
        }
        
        return features