"""
A.V.A.R. API Gateway
Central routing and load balancing for microservices
"""

import logging
import os
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration from environment
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:8080"
)

def get_cors_origins() -> List[str]:
    """Parse CORS origins from environment - no wildcards allowed"""
    origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
    # Remove wildcards for security
    return [o for o in origins if o != "*"]

# Service URLs from environment
AI_DETECTION_URL = os.getenv("AI_DETECTION_URL", "http://ai-detection-service:8001")
COMPETITION_SERVICE_URL = os.getenv("COMPETITION_SERVICE_URL", "http://competition-service:8080")

# HTTP client - managed with lifespan
http_client: Optional[httpx.AsyncClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage HTTP client lifecycle"""
    global http_client
    http_client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout for analysis
    logger.info("API Gateway started - HTTP client initialized")
    yield
    await http_client.aclose()
    logger.info("API Gateway shutdown - HTTP client closed")

app = FastAPI(
    title="A.V.A.R. API Gateway",
    description="Central API gateway for routing requests to microservices",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - properly configured with whitelist
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "A.V.A.R. API Gateway",
        "version": "1.0.0",
        "status": "operational",
        "services": {"ai_detection": AI_DETECTION_URL, "competition_management": COMPETITION_SERVICE_URL},
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if backend services are reachable
    services_health = {"gateway": "healthy", "ai_detection": "unknown", "competition_service": "unknown"}

    try:
        response = await http_client.get(f"{AI_DETECTION_URL}/health", timeout=5.0)
        services_health["ai_detection"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception:
        services_health["ai_detection"] = "unreachable"

    try:
        response = await http_client.get(f"{COMPETITION_SERVICE_URL}/health", timeout=5.0)
        services_health["competition_service"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception:
        services_health["competition_service"] = "unreachable"

    return {"status": "healthy", "timestamp": datetime.utcnow(), "services": services_health}


# === AI Detection Service Routes ===


@app.api_route("/api/v1/detect/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_ai_detection(path: str, request: Request):
    """
    Proxy requests to AI Detection Service
    Routes: /api/v1/detect/*
    """
    try:
        # Forward request to AI detection service
        url = f"{AI_DETECTION_URL}/{path}"

        # Get request body if present
        body = await request.body() if request.method in ["POST", "PUT"] else None

        # Forward request
        response = await http_client.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            content=body,
            params=request.query_params,
        )

        return JSONResponse(
            status_code=response.status_code,
            content=(
                response.json()
                if response.headers.get("content-type") == "application/json"
                else {"response": response.text}
            ),
        )

    except httpx.TimeoutException:
        logger.error("AI Detection service timeout")
        raise HTTPException(status_code=504, detail="AI Detection service timeout")
    except httpx.ConnectError:
        logger.error("AI Detection service unavailable")
        raise HTTPException(status_code=503, detail="AI Detection service unavailable")
    except Exception as e:
        logger.error(f"AI Detection proxy error: {str(e)}")
        # Don't expose internal error details in production
        detail = str(e) if DEBUG else "Service temporarily unavailable"
        raise HTTPException(status_code=500, detail=detail)


# === Competition Service Routes ===


@app.api_route("/api/v1/competitions/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_competition_service(path: str, request: Request):
    """
    Proxy requests to Competition Management Service
    Routes: /api/v1/competitions/*
    """
    try:
        url = f"{COMPETITION_SERVICE_URL}/{path}"

        body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None

        response = await http_client.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            content=body,
            params=request.query_params,
        )

        return JSONResponse(
            status_code=response.status_code,
            content=(
                response.json()
                if response.headers.get("content-type") == "application/json"
                else {"response": response.text}
            ),
        )

    except httpx.TimeoutException:
        logger.error("Competition service timeout")
        raise HTTPException(status_code=504, detail="Competition service timeout")
    except httpx.ConnectError:
        logger.error("Competition service unavailable")
        raise HTTPException(status_code=503, detail="Competition service unavailable")
    except Exception as e:
        logger.error(f"Competition service proxy error: {str(e)}")
        # Don't expose internal error details in production
        detail = str(e) if DEBUG else "Service temporarily unavailable"
        raise HTTPException(status_code=500, detail=detail)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler - sanitize errors for production"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    # Don't expose internal error details in production
    error_detail = str(exc) if DEBUG else "An unexpected error occurred"
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": error_detail}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
