FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for nftables and psutil
RUN apt-get update && apt-get install -y \
    nftables \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create necessary directories
RUN mkdir -p data snapshots static

# Expose NiftyWall port
EXPOSE 8080

# Run with Gunicorn and Uvicorn workers
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--timeout", "120"]
