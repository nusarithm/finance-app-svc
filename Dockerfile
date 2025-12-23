#############################################
# Multi-stage Dockerfile for small, performant
# FastAPI image (uvicorn + uvloop + httptools)
#############################################

FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Install build deps required for some Python wheels (we'll keep them out of final image)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential gcc git curl ca-certificates pkg-config \
       libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /wheels
COPY requirements.txt /tmp/requirements.txt

# Build wheels into /wheels so the final image can be minimal
RUN pip install --upgrade pip setuptools wheel \
    && pip wheel --no-cache-dir -w /wheels -r /tmp/requirements.txt


FROM python:3.11-slim AS final
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Runtime deps for OpenCV / easyocr etc (small list)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install - this avoids building packages inside final image
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && pip install --no-cache-dir uvloop httptools \
    && rm -rf /wheels /root/.cache/pip

# App code
WORKDIR /app
COPY . /app

# Create non-root user and ensure uploads dir exists
RUN groupadd -r app && useradd -r -g app app \
    && mkdir -p /app/uploads \
    && chown -R app:app /app

USER app
EXPOSE 1234

# Healthcheck (relies on /health endpoint in app)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://localhost:1234/health') or sys.exit(0)" || exit 1

# Default number of workers can be overridden with UVICORN_WORKERS env var
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 1234 --workers ${UVICORN_WORKERS:-2} --loop uvloop --http httptools"]
