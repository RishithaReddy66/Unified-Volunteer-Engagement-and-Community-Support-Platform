import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-dev-secret-change-in-production")
    JWT_SECRET = os.environ.get("JWT_SECRET", "jwt-dev-secret-change-in-production")
    JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", 24))
    MONGO_URI = os.environ.get("MONGO_URI", "")
    DEBUG = os.environ.get("FLASK_ENV") == "development"
