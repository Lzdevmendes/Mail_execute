from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class EmailCategory(str, Enum):
    """Email classification categories"""
    PRODUCTIVE = "produtivo"
    UNPRODUCTIVE = "improdutivo"


class EmailClassificationRequest(BaseModel):
    """Request model for email classification"""
    content: str = Field(..., min_length=10, max_length=10000, description="Email content to classify")
    source: str = Field(default="api", description="Source of the request")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class EmailClassificationResponse(BaseModel):
    """Response model for email classification"""
    category: str = Field(..., description="Classification category (produtivo/improdutivo)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence score")
    suggested_response: str = Field(..., description="Generated response text")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(..., description="Classification timestamp")
    model_used: str = Field(default="rule_based", description="Model used for classification")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="System status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(default="1.0.0", description="API version")
    ai_model_loaded: bool = Field(default=False, description="Whether AI model is loaded")
    uptime: float = Field(..., description="System uptime in seconds")


class MetricsResponse(BaseModel):
    """System metrics response model"""
    total_processed: int = Field(default=0, description="Total emails processed")
    productive_count: int = Field(default=0, description="Number of productive emails")
    unproductive_count: int = Field(default=0, description="Number of unproductive emails")
    average_processing_time: float = Field(default=0.0, description="Average processing time")
    last_processed: Optional[datetime] = Field(default=None, description="Last processing timestamp")


class FileUploadResponse(BaseModel):
    """File upload response model"""
    filename: str = Field(..., description="Uploaded filename")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="File MIME type")
    processed: bool = Field(default=False, description="Whether file was processed")
    content: Optional[str] = Field(default=None, description="Extracted content")
    error: Optional[str] = Field(default=None, description="Error message if any")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    timestamp: datetime = Field(..., description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


# Internal models for processing
class EmailContent(BaseModel):
    """Internal model for processed email content"""
    raw_content: str = Field(..., description="Raw email content")
    cleaned_content: str = Field(..., description="Cleaned email content")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    sentiment: Optional[str] = Field(default=None, description="Detected sentiment")
    urgency_score: float = Field(default=0.0, description="Urgency score 0-1")
    business_relevance: float = Field(default=0.0, description="Business relevance score 0-1")


class ClassificationResult(BaseModel):
    """Internal classification result"""
    category: str = Field(..., description="Classification category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reasoning: Optional[str] = Field(default=None, description="Classification reasoning")
    features_used: List[str] = Field(default_factory=list, description="Features used in classification")
    model_name: str = Field(..., description="Model used for classification")


class ResponseTemplate(BaseModel):
    """Template for generating responses"""
    category: str = Field(..., description="Email category")
    template: str = Field(..., description="Response template")
    variables: Dict[str, str] = Field(default_factory=dict, description="Template variables")
    tone: str = Field(default="professional", description="Response tone")


class EmailProcessingMetrics(BaseModel):
    """Email processing metrics tracking"""
    total_processed: int = Field(default=0, description="Total emails processed")
    productive_count: int = Field(default=0, description="Productive emails count")
    unproductive_count: int = Field(default=0, description="Unproductive emails count")
    average_processing_time: float = Field(default=0.0, description="Average processing time")
    average_confidence: float = Field(default=0.0, description="Average confidence score")
    last_processed_time: Optional[datetime] = Field(default=None, description="Last processing time")
    last_updated: Optional[datetime] = Field(default=None, description="Last updated time")
    start_time: datetime = Field(default_factory=datetime.now, description="Metrics start time")


# Validation helpers
@validator('content', allow_reuse=True)
def validate_content(cls, v):
    """Validate email content"""
    if not v or not v.strip():
        raise ValueError("Email content cannot be empty")
    if len(v.strip()) < 10:
        raise ValueError("Email content too short (minimum 10 characters)")
    return v.strip()


@validator('confidence', allow_reuse=True)
def validate_confidence(cls, v):
    """Validate confidence score"""
    if not 0.0 <= v <= 1.0:
        raise ValueError("Confidence must be between 0.0 and 1.0")
    return round(v, 3)


# Add validators to models
EmailClassificationRequest.validate_content = validate_content
EmailClassificationResponse.validate_confidence = validate_confidence
ClassificationResult.validate_confidence = validate_confidence