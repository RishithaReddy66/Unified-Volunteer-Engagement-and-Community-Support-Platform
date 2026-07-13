from flask import Blueprint, jsonify, g
from database import get_db
from middleware.auth import token_required, ngo_required, volunteer_required
from bson import ObjectId
from datetime import datetime, timezone

applications_bp = Blueprint("applications", __name__)

# Note: POST /events/:id/apply is handled in events.py to keep URL at /api/events/:id/apply


def serialize_application_with_event(app, event=None):
    a = {
        "id": str(app["_id"]),
        "eventId": str(app["eventId"]),
        "volunteerId": str(app["volunteerId"]),
        "status": app["status"],
        "createdAt": app["createdAt"].isoformat() if hasattr(app["createdAt"], "isoformat") else str(app["createdAt"]),
        "updatedAt": app["updatedAt"].isoformat() if hasattr(app["updatedAt"], "isoformat") else str(app["updatedAt"]),
    }
    if event:
        a["event"] = {
            "id": str(event["_id"]),
            "name": event.get("name", ""),
            "type": event.get("type", ""),
            "date": event.get("date", ""),
            "time": event.get("time", ""),
            "location": event.get("location", ""),
            "status": event.get("status", ""),
            "description": event.get("description", ""),
        }
    return a


# ─── Volunteer: my applications ────────────────────────────────────────────────

@applications_bp.route("/my", methods=["GET"])
@volunteer_required
def get_my_applications():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    apps = list(db.applications.find({"volunteerId": ObjectId(g.user_id)}).sort("createdAt", -1))
    event_ids = [a["eventId"] for a in apps]
    events = {e["_id"]: e for e in db.events.find({"_id": {"$in": event_ids}})}

    result = [serialize_application_with_event(a, event=events.get(a["eventId"])) for a in apps]
    return jsonify({"applications": result})


# ─── NGO: accept application ──────────────────────────────────────────────────

@applications_bp.route("/<app_id>/accept", methods=["POST"])
@ngo_required
def accept_application(app_id):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    try:
        oid = ObjectId(app_id)
    except Exception:
        return jsonify({"error": "Invalid application ID"}), 400

    app = db.applications.find_one({"_id": oid})
    if not app:
        return jsonify({"error": "Application not found"}), 404

    event = db.events.find_one({"_id": app["eventId"]})
    if not event or str(event["ngoId"]) != g.user_id:
        return jsonify({"error": "Not authorized"}), 403
    if event["status"] == "Completed":
        return jsonify({"error": "Cannot modify applications for completed events"}), 400
    if app["status"] != "Pending":
        return jsonify({"error": "Can only accept Pending applications"}), 400

    now = datetime.now(timezone.utc)
    db.applications.update_one({"_id": oid}, {"$set": {"status": "Accepted", "updatedAt": now}})
    app["status"] = "Accepted"
    app["updatedAt"] = now
    return jsonify({"application": serialize_application_with_event(app)})


# ─── NGO: reject application ──────────────────────────────────────────────────

@applications_bp.route("/<app_id>/reject", methods=["POST"])
@ngo_required
def reject_application(app_id):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    try:
        oid = ObjectId(app_id)
    except Exception:
        return jsonify({"error": "Invalid application ID"}), 400

    app = db.applications.find_one({"_id": oid})
    if not app:
        return jsonify({"error": "Application not found"}), 404

    event = db.events.find_one({"_id": app["eventId"]})
    if not event or str(event["ngoId"]) != g.user_id:
        return jsonify({"error": "Not authorized"}), 403
    if event["status"] == "Completed":
        return jsonify({"error": "Cannot modify applications for completed events"}), 400
    if app["status"] != "Pending":
        return jsonify({"error": "Can only reject Pending applications"}), 400

    now = datetime.now(timezone.utc)
    db.applications.update_one({"_id": oid}, {"$set": {"status": "Rejected", "updatedAt": now}})
    app["status"] = "Rejected"
    app["updatedAt"] = now
    return jsonify({"application": serialize_application_with_event(app)})
