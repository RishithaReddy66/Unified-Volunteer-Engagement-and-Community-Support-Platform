import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config
from database import init_db
from routes.auth import auth_bp
from routes.events import events_bp
from routes.applications import applications_bp

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

init_db(app)

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(events_bp, url_prefix="/api/events")
app.register_blueprint(applications_bp, url_prefix="/api/applications")


@app.route("/api")
def index():
    return jsonify({"message": "API Running"})


@app.route("/api/healthz")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_ENV") == "development")
