"""
A.V.A.R. API Gateway
Central routing and load balancing for microservices
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from datetime import datetime
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="A.V.A.R. API Gateway",
    description="Central API gateway for routing requests to microservices",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs from environment
AI_DETECTION_URL = os.getenv("AI_DETECTION_URL", "http://ai-detection-service:8001")
COMPETITION_SERVICE_URL = os.getenv("COMPETITION_SERVICE_URL", "http://competition-service:80")

# HTTP client configuration
http_client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout for analysis


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "A.V.A.R. API Gateway",
        "version": "1.0.0",
        "status": "operational",
        "services": {
            "ai_detection": AI_DETECTION_URL,
            "competition_management": COMPETITION_SERVICE_URL
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if backend services are reachable
    services_health = {
        "gateway": "healthy",
        "ai_detection": "unknown",
        "competition_service": "unknown"
    }

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

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": services_health
    }


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
            headers={k: v for k, v in request.headers.items() if k.lower() != 'host'},
            content=body,
            params=request.query_params
        )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.headers.get('content-type') == 'application/json' else {"response": response.text}
        )

    except Exception as e:
        logger.error(f"AI Detection proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


# === Competition Service Routes ===

@app.api_route("/api/v1/competitions/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_competition_service(path: str, request: Request):
    """
    Proxy requests to Competition Management Service
    Routes: /api/v1/competitions/*
    """
    try:
        url = f"{COMPETITION_SERVICE_URL}/{path}"

        body = await request.body() if request.method in ["POST", "PUT"] else None

        response = await http_client.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers.items() if k.lower() != 'host'},
            content=body,
            params=request.query_params
        )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.headers.get('content-type') == 'application/json' else {"response": response.text}
        )

    except Exception as e:
        logger.error(f"Competition service proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await http_client.aclose()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
