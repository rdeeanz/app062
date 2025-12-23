# Superset configuration file
import os
from datetime import timedelta

# Flask App Builder configuration
SECRET_KEY = os.getenv('SUPERSET_SECRET_KEY', 'supersecretkey123_very_long_random_string_here')

# Use PostgreSQL for Superset metadata
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres123@postgres:5432/superset_meta'

# CSRF - Disable for login issues
WTF_CSRF_ENABLED = False
FAB_CSRF_ENABLED = False

# ============================================
# SESSION CONFIGURATION - Critical for login
# ============================================
from flask_session import Session

# Use SQLAlchemy session (same DB as metadata)
SESSION_TYPE = 'sqlalchemy'
SESSION_SQLALCHEMY_TABLE = 'sessions'
SESSION_PERMANENT = True
PERMANENT_SESSION_LIFETIME = timedelta(days=1)
SESSION_USE_SIGNER = True
SESSION_KEY_PREFIX = 'superset_session:'

# Cookie settings
SESSION_COOKIE_NAME = 'superset_session'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_PATH = '/'
SESSION_COOKIE_DOMAIN = None  # Allow any domain

# Feature flags
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
}

# Allow database connections
PREVENT_UNSAFE_DB_CONNECTIONS = False

# Track modifications
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Webserver config
SUPERSET_WEBSERVER_PROTOCOL = "http"
SUPERSET_WEBSERVER_ADDRESS = "0.0.0.0"
SUPERSET_WEBSERVER_PORT = 8088

# Enable proxy fix
ENABLE_PROXY_FIX = True
PROXY_FIX_CONFIG = {"x_for": 1, "x_proto": 1, "x_host": 1, "x_prefix": 1}

# Public role
PUBLIC_ROLE_LIKE = "Gamma"

# Flask-Login
AUTH_TYPE = 1
