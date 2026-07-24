# ==============================================================================
# ResumeSphere AI — Production Multi-Stage Dockerfile (Python 3.11 Slim)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build & Dependencies Builder
# ------------------------------------------------------------------------------
FROM python:3.11-slim as builder

# Set environment variables for build efficiency
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system build tools required for native C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for clean dependency isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Final Secure Production Runtime Image
# ------------------------------------------------------------------------------
FROM python:3.11-slim as runner

# Define runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000 \
    APP_ENV=production \
    HF_HOME=/tmp/huggingface_cache

WORKDIR /app

# Install runtime C libraries required by PyMuPDF and curl for HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create a non-root application user and group for security
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser && \
    mkdir -p /app/backend/uploads /tmp/huggingface_cache && \
    chown -R appuser:appgroup /app /tmp/huggingface_cache

# Copy application source code with non-root ownership
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Expose HTTP port
EXPOSE 8000

# Container Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start FastAPI server using Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
