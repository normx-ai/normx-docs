"""
Configuration centralisée des logs pour l'application
"""
import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any


class JSONFormatter(logging.Formatter):
    """Formateur pour logs structurés en JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'process_id': record.process,
            'thread_id': record.thread,
        }
        
        # Ajouter des informations supplémentaires si disponibles
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_obj['request_id'] = record.request_id
        if hasattr(record, 'ip_address'):
            log_obj['ip_address'] = record.ip_address
        
        # Ajouter l'exception si présente
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "./logs/app.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    enable_console: bool = True
) -> None:
    """
    Configure le système de logging pour l'application
    
    Args:
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Chemin du fichier de log
        max_bytes: Taille maximale du fichier avant rotation
        backup_count: Nombre de fichiers de backup à conserver
        enable_console: Activer les logs dans la console
    """
    
    # Créer le répertoire de logs s'il n'existe pas
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configuration du logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Supprimer les handlers existants
    root_logger.handlers = []
    
    # Format pour la console (plus lisible)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Format JSON pour les fichiers
    json_formatter = JSONFormatter()
    
    # Handler pour fichier avec rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)
    
    # Handler pour la console
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_format)
        root_logger.addHandler(console_handler)
    
    # Handler pour les erreurs critiques (envoi par email en production)
    error_log_file = log_file.replace('.log', '_errors.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    root_logger.addHandler(error_handler)
    
    # Configurer les loggers spécifiques
    
    # Réduire le niveau de log pour les bibliothèques tierces
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('celery').setLevel(logging.INFO)
    
    # Logger pour les requêtes HTTP
    access_logger = logging.getLogger('access')
    access_handler = logging.handlers.RotatingFileHandler(
        log_file.replace('.log', '_access.log'),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    access_handler.setFormatter(json_formatter)
    access_logger.addHandler(access_handler)
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False
    
    # Logger pour la sécurité
    security_logger = logging.getLogger('security')
    security_handler = logging.handlers.RotatingFileHandler(
        log_file.replace('.log', '_security.log'),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    security_handler.setFormatter(json_formatter)
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.INFO)
    security_logger.propagate = False
    
    logging.info("Système de logging configuré avec succès")


def get_logger(name: str) -> logging.Logger:
    """
    Obtenir un logger configuré pour un module spécifique
    
    Args:
        name: Nom du module (généralement __name__)
    
    Returns:
        Logger configuré
    """
    return logging.getLogger(name)


# Middleware pour ajouter des informations contextuelles aux logs
class LoggingContextMiddleware:
    """Middleware pour ajouter le contexte de la requête aux logs"""
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        import uuid
        import contextvars
        
        # Générer un ID unique pour la requête
        request_id = str(uuid.uuid4())
        
        # Ajouter les informations au contexte de logging
        request_id_var = contextvars.ContextVar('request_id', default=None)
        request_id_var.set(request_id)
        
        # Logger la requête entrante
        access_logger = logging.getLogger('access')
        path = scope.get("path", "")
        method = scope.get("method", "")
        access_logger.info(f"Request {request_id}: {method} {path}")
        
        # Passer la requête à l'application
        await self.app(scope, receive, send)