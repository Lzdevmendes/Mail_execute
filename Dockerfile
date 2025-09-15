# Multi-stage build para reduzir tamanho final
FROM python:3.11-slim as builder

# Variáveis de ambiente para build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependências de build apenas no builder
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar em diretório separado
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage final - imagem limpa
FROM python:3.11-slim

# Variáveis de ambiente para produção
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    ENVIRONMENT=production \
    DEBUG=false \
    PATH=/root/.local/bin:$PATH

WORKDIR /app

# Instalar apenas dependências runtime essenciais
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar Python packages do builder
COPY --from=builder /root/.local /root/.local

# Copiar apenas código necessário
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Criar diretórios necessários
RUN mkdir -p /tmp/uploads /tmp/models_cache /tmp/logs

# Download NLTK data com cache otimizado
RUN python -c "import nltk; import os; os.makedirs('/tmp/nltk_data', exist_ok=True); nltk.data.path.append('/tmp/nltk_data'); nltk.download('punkt', download_dir='/tmp/nltk_data', quiet=True); nltk.download('stopwords', download_dir='/tmp/nltk_data', quiet=True); nltk.download('rslp', download_dir='/tmp/nltk_data', quiet=True)" || true

# Limpar cache Python
RUN find /root/.local -name "*.pyc" -delete \
    && find /root/.local -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

EXPOSE $PORT

CMD python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1