# Stage 1: Builder - Install build dependencies
FROM python:3.12-slim AS builder

WORKDIR /builder

RUN apt-get update && apt-get install -y \
    nftables \
    gcc \
    python3-dev \
    fail2ban \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime - Minimal image with app code
FROM python:3.12-slim

LABEL org.opencontainers.image.title="NiftyWall" \
      org.opencontainers.image.description="Professional web dashboard for managing nftables firewall" \
      org.opencontainers.image.version="3.4.0" \
      org.opencontainers.image.source="https://github.com/weby-homelab/niftywall" \
      org.opencontainers.image.licenses="GPLv3"

# Install runtime system dependencies (from builder to keep layer cache)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nftables \
    fail2ban \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy only the app code and static assets
COPY app/ ./app/
COPY static/ ./static/
COPY templates/ ./templates/
COPY VERSION .

# Create necessary directories
RUN mkdir -p data snapshots

# Default port
ENV PORT=8080
ENV DATA_DIR=/app/data
ENV SNAPSHOT_DIR=/app/snapshots
ENV TZ=Europe/Kyiv

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; port = os.getenv('PORT', '8080'); urllib.request.urlopen('http://localhost:' + port + '/api/system/status')" || exit 1

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--timeout", "120"]
