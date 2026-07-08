FROM python:3.11-slim

WORKDIR /app

# Dependências primeiro (aproveita cache de camadas).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código e interface web.
COPY backend/ ./backend/
COPY web/ ./web/

EXPOSE 8765

# Sobe a API unificada, que já serve a interface web na raiz.
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8765"]
