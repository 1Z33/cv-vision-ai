FROM python:3.11-slim

WORKDIR /app

# Installation dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Port exposé
EXPOSE 8000

# Migration et démarrage
CMD sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"