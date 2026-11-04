"""
CloudPulse Main Application Entrypoint.
FastAPI application with correlation ID tracking, Prometheus telemetry middleware,
structured logging, and comprehensive enterprise health probes.
"""

import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.logger import setup_logger, correlation_id_ctx
from app.models import RootResponse
from app.metrics import (
    APP_INFO,
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_IN_PROGRESS
)
from app.routers import health, metrics, system, simulation

settings = get_settings()
logger = setup_logger(
    name="cloudpulse-api",
    log_level=settings.LOG_LEVEL,
    environment=settings.ENVIRONMENT
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events (startup & graceful shutdown)."""
    # Startup: register app info metric
    APP_INFO.info({
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "service": settings.APP_NAME,
        "region": settings.AWS_REGION
    })
    logger.info(
        f"CloudPulse Platform starting up - version={settings.APP_VERSION}, "
        f"env={settings.ENVIRONMENT}, region={settings.AWS_REGION}"
    )
    yield
    # Graceful shutdown
    logger.info("CloudPulse Platform shutting down gracefully.")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Enable CORS for frontend/dashboard cross-origin queries
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def observability_and_correlation_middleware(request: Request, call_next):
    """
    Middleware providing:
    1. Correlation ID propagation (X-Correlation-ID header)
    2. Prometheus request duration and throughput metrics
    3. Structured access logging
    """
    # 1. Manage Correlation ID
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    token = correlation_id_ctx.set(correlation_id)

    # 2. Track Prometheus In-Progress Gauge
    endpoint = request.url.path
    method = request.method
    HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()

    start_time = time.time()
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    try:
        response: Response = await call_next(request)
        status_code = response.status_code
    except Exception as exc:
        logger.error(
            f"Unhandled exception during {method} {endpoint}: {str(exc)}",
            exc_info=True
        )
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "correlation_id": correlation_id
            }
        )
        status_code = response.status_code
    finally:
        duration = time.time() - start_time
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()

        # Update metrics
        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()

        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        # Attach Correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id
        correlation_id_ctx.reset(token)

        # Structured request logging
        logger.info(
            f"{method} {endpoint} {status_code} - {duration * 1000:.2f}ms",
            extra={
                "extra_fields": {
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "client_ip": request.client.host if request.client else "unknown"
                }
            }
        )

    return response


# --- Root Endpoint ---
@app.get(
    "/",
    response_model=RootResponse,
    tags=["Root"],
    summary="Application Root & Discovery",
    description="Returns platform overview, health check URL, and observability endpoints."
)
def root():
    """Root landing endpoint with system discovery metadata."""
    return RootResponse(
        name=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        status="healthy",
        docs_url="/docs",
        health_url="/health",
        metrics_url="/metrics"
    )


# --- Register Sub-Routers ---
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(system.router)
app.include_router(simulation.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

