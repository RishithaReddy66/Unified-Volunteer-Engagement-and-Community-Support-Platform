from functools import wraps
from flask import request, jsonify, g
from utils.jwt_utils import verify_token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing or malformed"}), 401

        token = auth_header.split(" ", 1)[1]
        payload = verify_token(token)

        if payload is None:
            return jsonify({"error": "Invalid or expired token"}), 401

        g.user_id = payload.get("user_id")
        g.role = payload.get("role")
        return f(*args, **kwargs)

    return decorated


def ngo_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.role != "ngo":
            return jsonify({"error": "NGO access required"}), 403
        return f(*args, **kwargs)

    return decorated


def volunteer_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.role != "volunteer":
            return jsonify({"error": "Volunteer access required"}), 403
        return f(*args, **kwargs)

    return decorated
