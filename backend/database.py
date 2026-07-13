import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError

_db = None
DEFAULT_DB_NAME = "volunteerbridge"


def init_db(app):
    global _db
    mongo_uri = app.config.get("MONGO_URI", "")

    if not mongo_uri:
        print("[WARNING] MONGO_URI not set. Database features will be unavailable.")
        return

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        # Use the database name from the URI if provided, otherwise fall back to default
        db_name = app.config.get("MONGO_DB_NAME", DEFAULT_DB_NAME)
        _db = client[db_name]
        print(f"[INFO] Connected to MongoDB successfully. Using database: '{db_name}'")
    except ConnectionFailure as e:
        print(f"[ERROR] MongoDB connection failed: {e}")
    except ConfigurationError as e:
        print(f"[ERROR] MongoDB configuration error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected database error: {e}")


def get_db():
    return _db
