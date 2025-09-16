import os
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = Field(default="Email Classification System", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    ENVIRONMENT: str = Field(default="development", description="Application environment")
    
    # Server Settings
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    RELOAD: bool = Field(default=False, description="Auto-reload on code changes")
    
    # AI Model Settings
    MODEL_NAME: str = Field(
        default="cardiffnlp/twitter-roberta-base-sentiment-latest",
        description="Hugging Face model for classification"
    )
    MODEL_CACHE_DIR: Optional[str] = Field(
        default="./models_cache",
        description="Directory to cache downloaded models"
    )
    MAX_LENGTH: int = Field(default=512, description="Maximum token length for model input")

    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", description="OpenAI model to use")
    USE_OPENAI: bool = Field(default=False, description="Enable OpenAI integration")
    OPENAI_MAX_TOKENS: int = Field(default=150, description="Maximum tokens for OpenAI response")
    OPENAI_TEMPERATURE: float = Field(default=0.3, description="OpenAI temperature for responses")
    
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, description="Maximum file size in bytes (10MB)")
    ALLOWED_FILE_EXTENSIONS: List[str] = Field(
        default=[".txt", ".pdf"],
        description="Allowed file extensions for upload"
    )
    UPLOAD_DIR: str = Field(default="./uploads", description="Directory for temporary file uploads")
    
    MIN_CONTENT_LENGTH: int = Field(default=10, description="Minimum content length for processing")
    MAX_CONTENT_LENGTH: int = Field(default=50000, description="Maximum content length for processing")
    DEFAULT_CONFIDENCE_THRESHOLD: float = Field(
        default=0.7,
        description="Default confidence threshold for classifications"
    )
    
    PRODUCTIVE_RESPONSES: List[str] = Field(
        default=[
            "Obrigado pela sua mensagem. Estou analisando sua solicitação e retornarei com uma resposta detalhada em breve.",
            "Recebi sua mensagem e entendo a urgência do assunto. Vou providenciar as informações solicitadas e te retorno hoje ainda.",
            "Sua solicitação foi recebida e está sendo processada pela nossa equipe. Você receberá uma atualização em até 24 horas.",
            "Agradeço pelo contato. Vou verificar as informações necessárias e te envio um retorno completo ainda hoje.",
            "Entendi sua demanda e vou trabalhar para resolve-la. Te mantenho informado sobre o progresso."
        ],
        description="Template responses for productive emails"
    )
    
    UNPRODUCTIVE_RESPONSES: List[str] = Field(
        default=[
            "Muito obrigado pela mensagem! Desejo tudo de melhor para você também.",
            "Agradeço pelas palavras gentis. Tenha um excelente dia!",
            "Obrigado pelo carinho! Fico feliz em receber sua mensagem.",
            "Muito obrigado! Desejo sucesso em todos os seus projetos.",
            "Agradeço pela mensagem. Tenha uma semana produtiva!"
        ],
        description="Template responses for unproductive emails"
    )
    
    # Security Settings
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials in CORS")
    CORS_ALLOW_METHODS: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed CORS methods"
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        default=["*"],
        description="Allowed CORS headers"
    )
    
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        description="Log message format"
    )
    LOG_FILE: Optional[str] = Field(default=None, description="Log file path (optional)")
    
    ENABLE_METRICS: bool = Field(default=True, description="Enable performance metrics collection")
    CACHE_RESPONSES: bool = Field(default=False, description="Enable response caching (not implemented)")
    MAX_CONCURRENT_REQUESTS: int = Field(default=10, description="Maximum concurrent processing requests")
    
    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.UPLOAD_DIR,
            self.MODEL_CACHE_DIR,
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return not self.DEBUG and self.ENVIRONMENT.lower() == "production"
    
    @property
    def allowed_file_types(self) -> List[str]:
        """Get allowed file MIME types based on extensions."""
        mime_types = {
            ".txt": "text/plain",
            ".pdf": "application/pdf"
        }
        return [mime_types.get(ext, "application/octet-stream") for ext in self.ALLOWED_FILE_EXTENSIONS]

settings = Settings()

settings.create_directories()