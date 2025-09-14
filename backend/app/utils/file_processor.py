import io
import os
import tempfile
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from PyPDF2 import PdfReader
from loguru import logger

from ..config import settings
from ..models.email_models import FileUploadResponse


class FileProcessor:
    """Handles file upload and content extraction for various file types."""
    
    SUPPORTED_EXTENSIONS = {'.txt', '.pdf'}
    MAX_PREVIEW_LENGTH = 200
    
    @staticmethod
    def validate_file(file: UploadFile) -> None:
        # Check if file was uploaded
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No file was uploaded"
            )
        
        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in FileProcessor.SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed types: {', '.join(FileProcessor.SUPPORTED_EXTENSIONS)}"
            )
        
        # Check file size (read content to get actual size)
        content = file.file.read()
        file.file.seek(0)  # Reset file pointer
        
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )
        
        if len(content) > settings.MAX_FILE_SIZE:
            max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {max_size_mb:.1f}MB"
            )
    
    @staticmethod
    def extract_text_from_txt(file_content: bytes) -> str:
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    text = file_content.decode(encoding)
                    logger.info(f"Successfully decoded TXT file using {encoding} encoding")
                    return text.strip()
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, use utf-8 with errors='replace'
            text = file_content.decode('utf-8', errors='replace')
            logger.warning("Used UTF-8 with error replacement for TXT file")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from TXT file: {str(e)}")
            raise Exception(f"Failed to process TXT file: {str(e)}")
    
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        try:
            # Create a BytesIO object from the file content
            pdf_file = io.BytesIO(file_content)
            
            # Create PDF reader
            pdf_reader = PdfReader(pdf_file)
            
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                raise Exception("Cannot process encrypted PDF files")
            
            # Extract text from all pages
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(page_text.strip())
                        logger.debug(f"Extracted text from PDF page {page_num}")
                except Exception as page_error:
                    logger.warning(f"Failed to extract text from PDF page {page_num}: {str(page_error)}")
                    continue
            
            if not text_content:
                raise Exception("No readable text found in PDF file")
            
            # Join all pages with double newline
            full_text = "\n\n".join(text_content)
            logger.info(f"Successfully extracted text from PDF ({len(pdf_reader.pages)} pages)")
            
            return full_text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF file: {str(e)}")
            raise Exception(f"Failed to process PDF file: {str(e)}")
    
    @classmethod
    async def process_uploaded_file(cls, file: UploadFile) -> FileUploadResponse:
        try:
            # Validate the file
            cls.validate_file(file)
            
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            file_extension = Path(file.filename).suffix.lower()
            
            logger.info(f"Processing uploaded file: {file.filename} ({file_size} bytes)")
            
            # Extract text based on file type
            try:
                if file_extension == '.txt':
                    extracted_text = cls.extract_text_from_txt(file_content)
                elif file_extension == '.pdf':
                    extracted_text = cls.extract_text_from_pdf(file_content)
                else:
                    raise Exception(f"Unsupported file type: {file_extension}")
                
                # Validate extracted content
                if not extracted_text.strip():
                    raise Exception("No readable content found in file")
                
                if len(extracted_text) < settings.MIN_CONTENT_LENGTH:
                    raise Exception(f"Content too short (minimum {settings.MIN_CONTENT_LENGTH} characters required)")
                
                # Create preview
                content_preview = extracted_text[:cls.MAX_PREVIEW_LENGTH]
                if len(extracted_text) > cls.MAX_PREVIEW_LENGTH:
                    content_preview += "..."
                
                logger.info(f"Successfully extracted {len(extracted_text)} characters from {file.filename}")
                
                return FileUploadResponse(
                    filename=file.filename,
                    file_size=file_size,
                    content_preview=content_preview,
                    extraction_success=True,
                    error_message=None
                )
                
            except Exception as extraction_error:
                logger.error(f"Content extraction failed for {file.filename}: {str(extraction_error)}")
                
                return FileUploadResponse(
                    filename=file.filename,
                    file_size=file_size,
                    content_preview="",
                    extraction_success=False,
                    error_message=str(extraction_error)
                )
                
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing file {file.filename if file else 'unknown'}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process uploaded file: {str(e)}"
            )
    
    @classmethod
    def get_file_info(cls, file: UploadFile) -> Dict[str, Any]:
        file_extension = Path(file.filename).suffix.lower() if file.filename else ""
        
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "file_extension": file_extension,
            "is_supported": file_extension in cls.SUPPORTED_EXTENSIONS
        }