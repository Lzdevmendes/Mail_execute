# Email Classification System Dockerfile
# Optimized for Railway deployment

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    ENVIRONMENT=production \
    DEBUG=false

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Create necessary directories with Railway-compatible paths
RUN mkdir -p /tmp/uploads /tmp/models_cache /tmp/logs

# Download NLTK data during build for Railway
RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('rslp', quiet=True)" || true

# Expose port (Railway will override with $PORT)
EXPOSE $PORT

# Command to run the application (Railway uses $PORT environment variable)
CMD python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1