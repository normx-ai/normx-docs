from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
import logging
import uuid
import time
from contextlib import asynccontextmanager
from typing import Optional

from app.core.config import settings
from app.core.security import limiter, rate_limit_handler
from app.core.logging_config import setup_logging, get_logger
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

# Contexte de démarrage/arrêt pour gérer les ressources
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting NormX Docs API...")
    try:
        # Ici vous pouvez initialiser des connexions DB, cache, etc.
        # await initialize_database()
        # await connect_redis()
        logger.info("NormX Docs API started successfully")
        yield
    finally:
        # Shutdown
        logger.info("Shutting down NormX Docs API...")
        # Fermer les connexions proprement
        # await close_database()
        # await disconnect_redis()
        logger.info("NormX Docs API shutdown complete")

app = FastAPI(
    title="NormX Docs API",
    description="API pour le suivi intelligent des dossiers clients - NormX Docs",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
    # Désactiver la documentation en production si nécessaire
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# Middleware pour filtrer les hosts autorisés (sécurité)
if not settings.DEBUG and settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Middleware pour les headers de sécurité
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    try:
        response = await call_next(request)
        
        # Headers de sécurité essentiels
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy (ajuster selon vos besoins)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "connect-src 'self' ws: wss: https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        
        # HSTS pour HTTPS (activer en production)
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        return response
        
    except Exception as e:
        logger.error(f"Error in security headers middleware: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )

# Middleware pour le logging et monitoring
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Générer un ID unique pour tracer la requête
    request_id = str(uuid.uuid4())
    
    # Ajouter l'ID à l'état de la requête pour l'utiliser dans les logs
    request.state.request_id = request_id
    
    # Récupérer l'IP client (en tenant compte des proxies)
    client_host = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("X-Forwarded-For")
    real_ip = forwarded_for.split(",")[0].strip() if forwarded_for else client_host
    
    # Logger la requête entrante
    logger.info(
        f"Request {request_id}: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": real_ip,
            "user_agent": request.headers.get("User-Agent", "unknown")
        }
    )
    
    # Mesurer le temps de traitement
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Calculer le temps de traitement
        process_time = time.time() - start_time
        
        # Logger la réponse
        logger.info(
            f"Request {request_id} completed in {process_time:.3f}s",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": process_time,
                "method": request.method,
                "path": request.url.path
            }
        )
        
        # Ajouter des headers de tracking
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request {request_id} failed after {process_time:.3f}s: {str(e)}",
            extra={
                "request_id": request_id,
                "error": str(e),
                "process_time": process_time,
                "method": request.method,
                "path": request.url.path
            }
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "request_id": request_id}
        )

# Ajouter le rate limiter à l'application
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Handler global pour les erreurs HTTP
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        f"HTTP exception for request {request_id}: {exc.status_code} - {exc.detail}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "request_id": request_id
        }
    )

# Handler pour les erreurs de validation
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"Validation error for request {request_id}",
        extra={
            "request_id": request_id,
            "errors": exc.errors(),
            "path": request.url.path,
            "method": request.method
        }
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "request_id": request_id
        }
    )

# Handler global pour toutes les autres exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"Unhandled exception for request {request_id}: {str(exc)}",
        extra={
            "request_id": request_id,
            "error": str(exc),
            "error_type": type(exc).__name__,
            "path": request.url.path
        },
        exc_info=True  # Inclure la stack trace
    )
    
    # En production, ne pas exposer les détails de l'erreur
    if settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
                "request_id": request_id
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal error occurred. Please try again later.",
                "request_id": request_id
            }
        )

# Configuration CORS stricte
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        expose_headers=["X-Request-ID"],  # Exposer l'ID de requête au frontend
        max_age=600
    )

# Monter les fichiers statiques (seulement si le dossier existe)
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    
    # Route pour le favicon
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        favicon_path = os.path.join(static_path, "favicon.svg")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path)
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Favicon not found"}
        )

# Inclusion des routes avec préfixe API versionnée
API_V1_PREFIX = "/api/v1"

app.include_router(health.router, prefix=f"{API_V1_PREFIX}/health", tags=["health"])
app.include_router(auth.router, prefix=f"{API_V1_PREFIX}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{API_V1_PREFIX}/users", tags=["users"])
app.include_router(dossiers.router, prefix=f"{API_V1_PREFIX}/dossiers", tags=["dossiers"])
app.include_router(alertes.router, prefix=f"{API_V1_PREFIX}/alertes", tags=["alertes"])
app.include_router(dashboard.router, prefix=f"{API_V1_PREFIX}/dashboard", tags=["dashboard"])
app.include_router(clients.router, prefix=f"{API_V1_PREFIX}/clients", tags=["clients"])
app.include_router(echeances.router, prefix=f"{API_V1_PREFIX}/echeances", tags=["echeances"])
app.include_router(suivi.router, prefix=f"{API_V1_PREFIX}/suivi", tags=["suivi"])
app.include_router(notifications.router, prefix=f"{API_V1_PREFIX}/notifications", tags=["notifications"])
app.include_router(cabinet_settings.router, prefix=f"{API_V1_PREFIX}/cabinet-settings", tags=["cabinet"])
app.include_router(two_factor.router, prefix=f"{API_V1_PREFIX}/2fa", tags=["2fa"])
app.include_router(websocket.router, prefix=API_V1_PREFIX, tags=["websocket"])

# Route racine
@app.get("/", tags=["root"])
async def root():
    return {
        "message": "Bienvenue sur l'API NormX Docs",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs" if settings.DEBUG else None,
        "health": f"{API_V1_PREFIX}/health"
    }

# Route pour la santé basique (sans authentification)
@app.get("/health", tags=["health"])
async def basic_health():
    return {
        "status": "healthy",
        "service": "NormX Docs API",
        "version": "1.0.0"
    }