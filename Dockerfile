FROM python:3.10-slim

WORKDIR /app

# Installation des dépendances système si nécessaire (ex: libpq pour psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copier le fichier des dépendances depuis le dossier backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le contenu du dossier backend dans le WORKDIR (/app)
COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]