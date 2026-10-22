import os #for grabbing from envi
from datetime import timedelta
from hashlib import sha256


def _session_key(admin_password):
    """SECRET_KEY if set, else one derived from the admin password so every
    gunicorn worker signs sessions identically."""
    explicit = os.environ.get('SECRET_KEY')
    if explicit:
        return explicit
    if admin_password:
        return sha256(('datalogger-session:' + admin_password).encode()).hexdigest()
    return os.urandom(24).hex()


class Config:
    ENV = 'development'
    DEBUG = True
    # The /admin area is disabled unless ADMIN_PASSWORD is set.
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    SECRET_KEY = _session_key(ADMIN_PASSWORD)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE') == '1'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///data/sensor.db'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)

class ProductionConfig(Config):
    DEBUG = False

class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUC = True

class TestingConfig(Config):
    TESTING = True