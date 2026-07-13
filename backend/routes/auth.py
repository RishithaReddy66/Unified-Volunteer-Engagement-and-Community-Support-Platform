from flask import Blueprint, jsonify, request, g
from database import get_db
from utils.jwt_utils import generate_token
from middleware.auth import token_required
import bcrypt

auth_bp = Blueprint("auth", __name__)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


@auth_bp.route("/login", methods=["POST"])
def login():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "")

    if not email or not password or role not in ("ngo", "volunteer"):
        return jsonify({"error": "email, password, and role (ngo or volunteer) are required"}), 400

    collection = "ngos" if role == "ngo" else "volunteers"
    user = db[collection].find_one({"email": email})

    if not user or not check_password(password, user.get("password", "")):
        return jsonify({"error": "Invalid email or password"}), 401

    token = generate_token(str(user["_id"]), role)
    return jsonify({
        "token": token,
        "role": role,
        "user": {
            "id": str(user["_id"]),
            "name": user.get("name", ""),
            "email": user.get("email", ""),
        }
    })


@auth_bp.route("/signup/ngo", methods=["POST"])
def signup_ngo():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    required = ["name", "email", "password", "phone", "address", "mission"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    email = data["email"].strip().lower()
    if db.ngos.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    doc = {
        "name": data["name"].strip(),
        "email": email,
        "password": hash_password(data["password"]),
        "phone": data.get("phone", ""),
        "address": data.get("address", ""),
        "mission": data.get("mission", ""),
        "website": data.get("website", ""),
        "role": "ngo",
    }
    result = db.ngos.insert_one(doc)
    token = generate_token(str(result.inserted_id), "ngo")

    return jsonify({
        "token": token,
        "role": "ngo",
        "user": {"id": str(result.inserted_id), "name": doc["name"], "email": doc["email"]}
    }), 201


@auth_bp.route("/signup/volunteer", methods=["POST"])
def signup_volunteer():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    required = ["name", "email", "password", "phone", "location"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    email = data["email"].strip().lower()
    if db.volunteers.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    doc = {
        "name": data["name"].strip(),
        "email": email,
        "password": hash_password(data["password"]),
        "phone": data.get("phone", ""),
        "location": data.get("location", ""),
        "skills": data.get("skills", []),
        "description": data.get("description", ""),
        "rating": None,
        "role": "volunteer",
    }
    result = db.volunteers.insert_one(doc)
    token = generate_token(str(result.inserted_id), "volunteer")

    return jsonify({
        "token": token,
        "role": "volunteer",
        "user": {"id": str(result.inserted_id), "name": doc["name"], "email": doc["email"]}
    }), 201


@auth_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile():
    from bson import ObjectId
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    collection = "ngos" if g.role == "ngo" else "volunteers"
    allowed_ngo = ["name", "phone", "address", "mission", "website"]
    allowed_vol = ["name", "phone", "location", "skills", "description"]
    allowed = allowed_ngo if g.role == "ngo" else allowed_vol

    update = {}
    for field in allowed:
        if field in data:
            update[field] = data[field]

    if not update:
        return jsonify({"error": "No valid fields to update"}), 400

    from datetime import datetime, timezone
    update["updatedAt"] = datetime.now(timezone.utc)

    db[collection].update_one({"_id": ObjectId(g.user_id)}, {"$set": update})
    user = db[collection].find_one({"_id": ObjectId(g.user_id)})
    user["_id"] = str(user["_id"])
    user.pop("password", None)
    return jsonify({"user": user, "role": g.role})


@auth_bp.route("/me", methods=["GET"])
@token_required
def get_me():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    from bson import ObjectId
    collection = "ngos" if g.role == "ngo" else "volunteers"
    user = db[collection].find_one({"_id": ObjectId(g.user_id)})

    if not user:
        return jsonify({"error": "User not found"}), 404

    user["_id"] = str(user["_id"])
    user.pop("password", None)
    return jsonify({"user": user, "role": g.role})
