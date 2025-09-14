# Email Classification System Dockerfile
# Multi-stage build for optimized production deployment

FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .
COPY backend/requirements.txt ./backend/

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/app/.local

# Make sure scripts in .local are usable
ENV PATH=/home/app/.local/bin:$PATH

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY requirements.txt .

# Create necessary directories
RUN mkdir -p uploads models_cache logs && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Download NLTK data during build (optional, can be done at runtime)
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('rslp')" || true

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Command to run the application
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]