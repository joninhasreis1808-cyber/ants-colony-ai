# Ant's 6.0 — imagem de nuvem (enxuta, free-tier friendly).
FROM python:3.11-slim

WORKDIR /app

# tesseract: OCR opcional usado pela percepção; curl: healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr curl \
    && rm -rf /var/lib/apt/lists/*

# Dependências enxutas primeiro (aproveita cache de camadas).
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt

# Código e interface web (a API serve web/ na raiz).
COPY backend/ ./backend/
COPY web/ ./web/

# A nuvem injeta $PORT; local usa 8765.
ENV PORT=8765
EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT:-8765}/health" || exit 1

# shell form para expandir $PORT em runtime.
CMD uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8765}
