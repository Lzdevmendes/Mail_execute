import asyncio
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from loguru import logger

from .config import settings
from .models.email_models import (
    EmailClassificationRequest,
    EmailClassificationResponse,
    EmailProcessingMetrics,
    HealthCheckResponse,
    ErrorResponse,
    FileUploadResponse,
    EmailSource
)
from .services.email_classifier import email_classifier
from .utils.file_processor import FileProcessor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Email Classification System...")
    
    try:
        # Initialize AI model
        await email_classifier.initialize_model()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        # Continue without AI model - will fall back to rule-based classification
    
    yield
    
    # Shutdown
    logger.info("Shutting down Email Classification System...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema para classificação automática de emails e geração de respostas",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Configure static files and templates
frontend_path = Path(__file__).parent.parent.parent / "frontend"
static_path = frontend_path / "static"
templates_path = frontend_path / "templates"

if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

templates = Jinja2Templates(directory=str(templates_path))

# Configure logging
logger.configure(
    handlers=[
        {
            "sink": "sys.stdout",
            "format": settings.LOG_FORMAT,
            "level": settings.LOG_LEVEL
        }
    ]
)

if settings.LOG_FILE:
    logger.add(
        settings.LOG_FILE,
        format=settings.LOG_FORMAT,
        level=settings.LOG_LEVEL,
        rotation="1 day",
        retention="7 days"
    )


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "details": {"status_code": exc.status_code, "path": str(request.url)}
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with structured error responses."""
    logger.error(f"Unhandled exception in {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An internal server error occurred",
            "details": {"path": str(request.url)} if not settings.is_production else None
        }
    )


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing information."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} ({process_time:.3f}s)")
    
    return response


# Routes
@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def read_root(request: Request):
    """Serve the main application page."""
    if templates_path.exists() and (templates_path / "index.html").exists():
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        return HTMLResponse(content="""
        <html>
            <head>
                <title>Email Classification System</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .header { text-align: center; margin-bottom: 40px; }
                    .api-info { background: #f5f5f5; padding: 20px; border-radius: 8px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📧 Sistema de Classificação de Emails</h1>
                        <p>Classificação Automática de Emails</p>
                    </div>
                    <div class="api-info">
                        <h2>API Documentation</h2>
                        <p>A interface web está sendo carregada...</p>
                        <p>Enquanto isso, você pode acessar:</p>
                        <ul>
                            <li><a href="/docs">Documentação da API (Swagger UI)</a></li>
                            <li><a href="/redoc">Documentação da API (ReDoc)</a></li>
                            <li><a href="/health">Status da Aplicação</a></li>
                        </ul>
                    </div>
                </div>
            </body>
        </html>
        """)


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Check application health status."""
    return HealthCheckResponse(
        status="healthy",
        version=settings.APP_VERSION,
        ai_model_loaded=email_classifier.is_model_loaded
    )


@app.post("/classify", response_model=EmailClassificationResponse, tags=["Classification"])
async def classify_email_text(request: EmailClassificationRequest):
    """
    Classify email content directly from text input.
    
    - **content**: Email text content to classify
    - **source**: Source of the email content (default: text_input)
    - **metadata**: Optional metadata about the email
    """
    try:
        logger.info(f"Received text classification request (length: {len(request.content)})")
        
        result = await email_classifier.classify_email(request)
        
        logger.info(f"Text classification completed: {result.category.value} (confidence: {result.confidence:.3f})")
        
        return result
        
    except ValueError as e:
        logger.warning(f"Text classification validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Text classification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@app.post("/classify/file", response_model=EmailClassificationResponse, tags=["Classification"])
async def classify_email_file(file: UploadFile = File(...)):
    """
    Classify email content from uploaded file (.txt or .pdf).
    
    - **file**: Upload a .txt or .pdf file containing email content
    """
    try:
        logger.info(f"Received file classification request: {file.filename}")
        
        # Validate file
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file was uploaded")
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in {'.txt', '.pdf'}:
            raise HTTPException(status_code=400, detail="Only .txt and .pdf files are supported")
        
        # Read file content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Extract text based on file type
        if file_extension == '.txt':
            email_content = FileProcessor.extract_text_from_txt(content)
        else:  # .pdf
            email_content = FileProcessor.extract_text_from_pdf(content)
        
        if not email_content.strip():
            raise HTTPException(status_code=400, detail="No readable content found in file")
        
        # Create classification request
        classification_request = EmailClassificationRequest(
            content=email_content,
            source=EmailSource.TXT_FILE if file_extension == '.txt' else EmailSource.PDF_FILE,
            metadata={"filename": file.filename, "file_size": len(content)}
        )
        
        # Classify the content
        result = await email_classifier.classify_email(classification_request)
        
        logger.info(f"File classification completed: {result.category.value} (confidence: {result.confidence:.3f})")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File classification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File classification failed: {str(e)}")


@app.post("/upload", response_model=FileUploadResponse, tags=["File Processing"])
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a file to extract text content.
    
    - **file**: Upload a .txt or .pdf file
    """
    try:
        logger.info(f"Received file upload request: {file.filename}")
        
        result = await FileProcessor.process_uploaded_file(file)
        
        logger.info(f"File upload processed: {file.filename} (success: {result.extraction_success})")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@app.post("/classify/batch", response_model=List[EmailClassificationResponse], tags=["Classification"])
async def classify_multiple_emails(requests: List[EmailClassificationRequest]):
    """
    Classify multiple emails in batch.
    
    - **requests**: List of email classification requests
    """
    try:
        logger.info(f"Received batch classification request for {len(requests)} emails")
        
        if len(requests) == 0:
            raise HTTPException(status_code=400, detail="No emails provided for classification")
        
        if len(requests) > 50:  # Limit batch size
            raise HTTPException(status_code=400, detail="Batch size too large (maximum 50 emails)")
        
        results = await email_classifier.classify_multiple_emails(requests)
        
        logger.info(f"Batch classification completed: {len(results)} results")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch classification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch classification failed: {str(e)}")


@app.get("/metrics", response_model=EmailProcessingMetrics, tags=["Metrics"])
async def get_processing_metrics():
    """Get current processing metrics and statistics."""
    return email_classifier.get_metrics()


@app.post("/metrics/reset", tags=["Metrics"])
async def reset_processing_metrics():
    """Reset processing metrics (useful for testing)."""
    email_classifier.reset_metrics()
    return {"message": "Processing metrics reset successfully"}


@app.get("/status", tags=["Health"])
async def get_status():
    """Get detailed application status."""
    metrics = email_classifier.get_metrics()
    
    return {
        "application": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
            "environment": "production" if settings.is_production else "development"
        },
        "ai_model": {
            "loaded": email_classifier.is_model_loaded,
            "model_name": settings.MODEL_NAME
        },
        "processing": {
            "total_processed": metrics.total_processed,
            "productive_emails": metrics.productive_count,
            "unproductive_emails": metrics.unproductive_count,
            "average_confidence": round(metrics.average_confidence, 3),
            "average_processing_time": round(metrics.average_processing_time, 4)
        },
        "configuration": {
            "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
            "allowed_extensions": settings.ALLOWED_FILE_EXTENSIONS,
            "max_content_length": settings.MAX_CONTENT_LENGTH,
            "min_content_length": settings.MIN_CONTENT_LENGTH
        }
    }


# Development server startup
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )