# ---------- STAGE: builder ----------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH

WORKDIR /app

# Dependências de sistema necessárias apenas para construir wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas requirements (otimiza cache Docker)
COPY requirements-production.txt ./requirements.txt

# Atualiza pip e cria wheels para evitar recompilar no final
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip wheel --no-cache-dir -r requirements.txt -w /wheels

# Instalar a partir das wheels para garantir consistência e reduzir recompilação
RUN pip install --no-index --find-links /wheels --no-cache-dir -r requirements.txt \
    --prefix=/root/.local

# ---------- STAGE: final ----------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH \
    NLTK_DATA=/usr/local/share/nltk_data \
    PORT=8000 \
    ENVIRONMENT=production \
    DEBUG=false

WORKDIR /app

# Instalar runtime system packages necessários (OCR, PDF rendering, libs de runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar pacotes Python instalados do builder
COPY --from=builder /root/.local /root/.local

# Copiar apenas o que é necessário da aplicação
# Ajuste estes COPY conforme sua estrutura real (minimize arquivos copiados)
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY requirements-production.txt ./requirements-production.txt

# NÃO copie .env! Use variáveis de ambiente no provedor.
# COPY .env ./

# Criar diretórios necessários em runtime
RUN mkdir -p /tmp/uploads /tmp/models_cache /tmp/logs $NLTK_DATA

# Baixar recursos NLTK para diretório persistente e pronto para uso
RUN python - <<'PY'
import nltk, os
nltk.data.path.append(os.environ.get('NLTK_DATA'))
nltk.download('punkt', download_dir=os.environ.get('NLTK_DATA'), quiet=True)
nltk.download('stopwords', download_dir=os.environ.get('NLTK_DATA'), quiet=True)
nltk.download('rslp', download_dir=os.environ.get('NLTK_DATA'), quiet=True)
PY

# Limpeza (apenas arquivos .pyc e caches)
RUN find /root/.local -name "*.pyc" -delete \
 && find /root/.local -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

EXPOSE ${PORT}

# HEALTHCHECK opcional (ajuste o endpoint conforme sua app)
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# ENTRYPOINT / CMD (use gunicorn em produção se preferir)
# Exemplo com gunicorn (recomendado para múltiplos workers):
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "backend.app.main:app", "-w", "4", "-b", "0.0.0.0:8000"]
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "uvloop"]
