FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-server.txt ./
RUN pip install --no-cache-dir -r requirements-server.txt

COPY . .

EXPOSE 10000

CMD ["sh", "-c", "cd 'Truthdoc AI' && BACKEND_HOST=0.0.0.0 BACKEND_PORT=${PORT:-10000} python backend.py"]
