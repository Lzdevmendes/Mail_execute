import io
import os
import tempfile
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from PyPDF2 import PdfReader
from loguru import logger

# OCR dependencies (optional)
try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_bytes
    OCR_AVAILABLE = True
    logger.info("OCR capabilities available (pytesseract + pdf2image)")
except ImportError as e:
    pytesseract = None
    Image = None
    convert_from_bytes = None
    OCR_AVAILABLE = False
    logger.warning(f"OCR not available: {e}. Install with: pip install pytesseract Pillow pdf2image")

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
    def extract_text_with_ocr(file_content: bytes) -> str:
        """Extract text from PDF using OCR (for image-based PDFs)."""
        if not OCR_AVAILABLE:
            raise Exception("OCR not available. Install: pip install pytesseract Pillow pdf2image")

        try:
            # Convert PDF pages to images
            logger.info("Converting PDF to images for OCR processing...")
            images = convert_from_bytes(file_content, dpi=200, fmt='JPEG')

            if not images:
                raise Exception("Could not convert PDF to images")

            # Extract text from each page using OCR
            text_content = []
            for page_num, image in enumerate(images, 1):
                try:
                    # Configure tesseract for better Portuguese recognition
                    custom_config = r'--oem 3 --psm 6 -l por+eng'
                    page_text = pytesseract.image_to_string(image, config=custom_config)

                    if page_text.strip():
                        text_content.append(page_text.strip())
                        logger.debug(f"OCR extracted text from page {page_num} ({len(page_text)} chars)")
                    else:
                        logger.warning(f"No text found on page {page_num} via OCR")

                except Exception as ocr_error:
                    logger.warning(f"OCR failed for page {page_num}: {str(ocr_error)}")
                    continue

            if not text_content:
                raise Exception("No text could be extracted via OCR")

            # Join all pages
            full_text = "\n\n".join(text_content)

            # Check if OCR mistakenly extracted HTML (sometimes happens with corrupted PDFs)
            if full_text.strip().startswith('<!DOCTYPE html>') or '<html>' in full_text[:500]:
                logger.warning("OCR extracted HTML content, PDF may be corrupted or contain embedded web content")
                raise Exception("PDF contains HTML content and cannot be processed as text document")

            logger.info(f"OCR successfully extracted text from {len(images)} pages ({len(full_text)} chars)")

            return full_text.strip()

        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            raise Exception(f"OCR processing failed: {str(e)}")

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

            # Extract text from all pages (traditional method)
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

            # If traditional extraction found text, use it
            if text_content:
                full_text = "\n\n".join(text_content)
                logger.info(f"Successfully extracted text from PDF ({len(pdf_reader.pages)} pages)")
                return full_text.strip()

            # If no text found and OCR is available, try OCR
            if OCR_AVAILABLE:
                logger.info("No text found with traditional extraction, trying OCR...")
                return FileProcessor.extract_text_with_ocr(file_content)
            else:
                raise Exception("No readable text found in PDF file. Install OCR dependencies for image-based PDFs: pip install pytesseract Pillow pdf2image")

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

                # Intelligent truncation for very long texts
                if len(extracted_text) > settings.MAX_CONTENT_LENGTH:
                    logger.warning(f"Content too long ({len(extracted_text)} chars), truncating to {settings.MAX_CONTENT_LENGTH}")
                    # Keep first part + last part to preserve context
                    first_part = extracted_text[:settings.MAX_CONTENT_LENGTH // 2]
                    last_part = extracted_text[-(settings.MAX_CONTENT_LENGTH // 2):]
                    extracted_text = first_part + "\n\n[... CONTEÚDO TRUNCADO ...]\n\n" + last_part
                
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