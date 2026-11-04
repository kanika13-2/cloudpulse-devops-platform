# ==============================================================================
# CloudPulse Containerfile - Multi-Stage Enterprise Production Image
# Security Hardened: Non-Root User (UID 10001), Minimal Attack Surface, Healthchecks
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment to isolate wheels
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ------------------------------------------------------------------------------
# Stage 2: Runtime Minimal Distroless-like Image
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runner

# Metadata labels for OCI compliance & AWS ECR tracking
LABEL maintainer="CloudPulse DevOps Team" \
      org.opencontainers.image.title="CloudPulse Platform" \
      org.opencontainers.image.description="AWS Cloud Infrastructure & Intelligent DevOps Automation Platform" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="CloudPulse" \
      org.opencontainers.image.licenses="Apache-2.0"

# Set runtime environment flags
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production \
    PORT=8000 \
    HOST=0.0.0.0

# Install runtime utilities (curl for container health checks) & cleanup
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user and group with explicit UID/GID
RUN groupadd -g 10001 cloudpulse && \
    useradd -u 10001 -g cloudpulse -m -s /bin/bash cloudpulse

WORKDIR /app

# Copy virtualenv from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application source code
COPY --chown=cloudpulse:cloudpulse app /app/app

# Ensure proper permission boundaries
RUN chown -R cloudpulse:cloudpulse /app

# Switch to non-root user
USER 10001:10001

# Expose internal listening port
EXPOSE 8000

# Docker Healthcheck instruction
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch application with production ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

