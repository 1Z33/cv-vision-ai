FROM python:3.10-slim

# Dépendances système : Tesseract OCR + Poppler (pdf2image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

# Vérification Tesseract au démarrage (build-time)
RUN python -c "import pytesseract; print('Tesseract:', pytesseract.get_tesseract_version())"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
