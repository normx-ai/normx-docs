from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import os
import logging

from app.core.config import settings
from app.core.security import limiter, rate_limit_handler
from app.core.logging_config import setup_logging, get_logger, LoggingContextMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.api import health, auth, users, dossiers, alertes, dashboard, websocket, clients, echeances, suivi, notifications, cabinet_settings, two_factor
from slowapi.errors import RateLimitExceeded

# Configure logging avec notre système
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file=settings.LOG_FILE,
    max_bytes=settings.LOG_MAX_SIZE_MB * 1024 * 1024,
    backup_count=settings.LOG_BACKUP_COUNT,
    enable_console=settings.DEBUG
)
logger = get_logger(__name__)

app = FastAPI(
    title="NormX Docs API",
    description="API pour le suivi intelligent des dossiers clients - NormX Docs",
    version="1.0.0",
    debug=settings.DEBUG,
)

# Ajouter le rate limiter à l'application
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Add custom exception handler for validation errors (temporary for debugging)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error on {request.method} {request.url.path}")
    logger.error(f"Validation errors: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# Ajouter les middlewares de sécurité et logging
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingContextMiddleware)

# Configuration CORS stricte
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        max_age=600
    )

# Monter les fichiers statiques
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Route pour le favicon
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(static_path, "favicon.svg"))

# Inclusion des routes
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(dossiers.router, prefix="/api/v1/dossiers", tags=["dossiers"])
app.include_router(alertes.router, prefix="/api/v1/alertes", tags=["alertes"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(clients.router, prefix="/api/v1/clients", tags=["clients"])
app.include_router(echeances.router, prefix="/api/v1/echeances", tags=["echeances"])
app.include_router(suivi.router, prefix="/api/v1/suivi", tags=["suivi"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(cabinet_settings.router, prefix="/api/v1/cabinet-settings", tags=["cabinet"])
app.include_router(two_factor.router, prefix="/api/v1/2fa", tags=["2fa"])
app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])


@app.get("/")
async def root():
    return {
        "message": "Bienvenue sur l'API NormX Docs",
        "version": "1.0.0",
        "docs": "/docs",
    }