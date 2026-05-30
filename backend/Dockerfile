# Backend FastAPI (Frente 5) — orquestrador AstroCopilot
FROM python:3.12-slim

# Evita .pyc e garante logs sem buffer (úteis no docker logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências primeiro (melhor cache de camadas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

EXPOSE 8000

# Sobe a API. Em produção troque --reload por workers.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
