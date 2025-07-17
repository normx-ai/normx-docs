"""
Configuration Hypercorn pour NormX Docs
"""
import os
from hypercorn.config import Config

config = Config()

# Binding
config.bind = ["0.0.0.0:8000"]

# Workers
config.workers = int(os.getenv("WEB_CONCURRENCY", "4"))

# Keep alive
config.keep_alive_timeout = 120

# Reload
config.use_reloader = os.getenv("ENV", "development") == "development"

# Access log
config.accesslog = "-"
config.errorlog = "-"

# SSL (pour production)
# config.certfile = "/path/to/cert.pem"
# config.keyfile = "/path/to/key.pem"

# Graceful timeout
config.graceful_timeout = 30

# Application
config.application_path = "app.main:app"