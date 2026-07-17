FROM python:3.12-slim

WORKDIR /app

# System deps: build tools for some wheels, ffmpeg for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    ffmpeg \
    libpq-dev \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads recordings transcripts logs chroma_db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
