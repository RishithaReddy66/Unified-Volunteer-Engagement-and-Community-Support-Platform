from flask import Blueprint, jsonify, request, g
from database import get_db
from middleware.auth import token_required, ngo_required, volunteer_required
from bson import ObjectId
from datetime import datetime, timezone

events_bp = Blueprint("events", __name__)


def _iso(val):
    if val is None:
        return None
    return val.isoformat() if hasattr(val, "isoformat") else str(val)


def serialize_event(event, ngo_name=None):
    e = {
        "id": str(event["_id"]),
        "ngoId": str(event["ngoId"]),
        "name": event["name"],
        "type": event["type"],
        "date": event["date"],
        "time": event["time"],
        "location": event["location"],
        "description": event.get("description", ""),
        "status": event["status"],
        "createdAt": _iso(event.get("createdAt")),
        "updatedAt": _iso(event.get("updatedAt")),
    }
    if ngo_name is not None:
        e["ngoName"] = ngo_name
    return e


def serialize_application(app, volunteer=None):
    a = {
        "id": str(app["_id"]),
        "eventId": str(app["eventId"]),
        "volunteerId": str(app["volunteerId"]),
        "status": app["status"],
        "createdAt": _iso(app.get("createdAt")),
        "updatedAt": _iso(app.get("updatedAt")),
    }
    if volunteer:
        a["volunteer"] = {
            "id": str(volunteer["_id"]),
            "name": volunteer.get("name", ""),
            "email": volunteer.get("email", ""),
            "phone": volunteer.get("phone", ""),
            "location": volunteer.get("location", ""),
            "skills": volunteer.get("skills", []),
            "description": volunteer.get("description", ""),
            "rating": volunteer.get("rating"),
        }
    return a


# ─── Stats (role-aware) ──────────────────────────────────────────────────────

@events_bp.route("/stats", methods=["GET"])
@token_required
def get_stats():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    user_oid = ObjectId(g.user_id)

    if g.role == "ngo":
        events = list(db.events.find({"ngoId": user_oid}))
        event_ids = [e["_id"] for e in events]
        total_apps = db.applications.count_documents({"eventId": {"$in": event_ids}}) if event_ids else 0
        total_accepted = db.applications.count_documents({"eventId": {"$in": event_ids}, "status": "Accepted"}) if event_ids else 0
        return jsonify({
            "totalEvents": len(events),
            "openEvents": sum(1 for e in events if e["status"] == "Open"),
            "closedEvents": sum(1 for e in events if e["status"] == "Applications Closed"),
            "completedEvents": sum(1 for e in events if e["status"] == "Completed"),
            "totalApplications": total_apps,
            "totalAccepted": total_accepted,
        })
    else:
        apps = list(db.applications.find({"volunteerId": user_oid}))
        accepted = sum(1 for a in apps if a["status"] == "Accepted")
        rejected = sum(1 for a in apps if a["status"] == "Rejected")
        pending = sum(1 for a in apps if a["status"] == "Pending")
        event_ids = [a["eventId"] for a in apps if a["status"] == "Accepted"]
        completed_participated = 0
        if event_ids:
            completed_participated = db.events.count_documents({"_id": {"$in": event_ids}, "status": "Completed"})
        return jsonify({
            "totalApplications": len(apps),
            "accepted": accepted,
            "rejected": rejected,
            "pending": pending,
            "completedParticipated": completed_participated,
        })


# ─── NGO: create event ───────────────────────────────────────────────────────

@events_bp.route("/create", methods=["POST"])
@ngo_required
def create_event():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    required = ["name", "type", "date", "time", "location"]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    now = datetime.now(timezone.utc)
    event = {
        "ngoId": ObjectId(g.user_id),
        "name": data["name"].strip(),
        "type": data["type"].strip(),
        "date": data["date"],
        "time": data["time"],
        "location": data["location"].strip(),
        "description": data.get("description", "").strip(),
        "status": "Open",
        "createdAt": now,
        "updatedAt": now,
    }
    result = db.events.insert_one(event)
    event["_id"] = result.inserted_id
    return jsonify({"event": serialize_event(event)}), 201


# ─── NGO: own events ─────────────────────────────────────────────────────────

@events_bp.route("/my", methods=["GET"])
@ngo_required
def get_my_events():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    events = list(db.events.find({"ngoId": ObjectId(g.user_id)}).sort("createdAt", -1))
    return jsonify({"events": [serialize_event(e) for e in events]})


# ─── Volunteer: browse open events ───────────────────────────────────────────

@events_bp.route("/open", methods=["GET"])
@token_required
def get_open_events():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    query = {"status": "Open"}

    search = request.args.get("q", "").strip()
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"type": {"$regex": search, "$options": "i"}},
            {"location": {"$regex": search, "$options": "i"}},
        ]

    type_filter = request.args.get("type", "").strip()
    if type_filter:
        query["type"] = {"$regex": type_filter, "$options": "i"}

    location_filter = request.args.get("location", "").strip()
    if location_filter:
        query["location"] = {"$regex": location_filter, "$options": "i"}

    events = list(db.events.find(query).sort("createdAt", -1))

    ngo_ids = list({e["ngoId"] for e in events})
    ngos = {n["_id"]: n for n in db.ngos.find({"_id": {"$in": ngo_ids}})}

    result = []
    for e in events:
        ngo = ngos.get(e["ngoId"])
        ngo_name = ngo["name"] if ngo else "Unknown NGO"
        result.append(serialize_event(e, ngo_name=ngo_name))

    return jsonify({"events": result})


# ─── Event details (shared) ───────────────────────────────────────────────────

@events_bp.route("/<event_id>", methods=["GET"])
@token_required
def get_event(event_id):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    try:
        oid = ObjectId(event_id)
    except Exception:
        return jsonify({"error": "Invalid event ID"}), 400

    event = db.events.find_one({"_id": oid})
    if not event:
        return jsonify({"error": "Event not found"}), 404

    ngo = db.ngos.find_one({"_id": event["ngoId"]})
    ngo_name = ngo["name"] if ngo else "Unknown NGO"

    data = serialize_event(event, ngo_name=ngo_name)

    # If volunteer, include their application for this event
    if g.role == "volunteer":
        app = db.applications.find_one({
            "eventId": oid,
            "volunteerId": ObjectId(g.user_id)
        })
        data["myApplication"] = serialize_application(app) if app else None

    return jsonify({"event": data})


# ─── Volunteer: apply to event ───────────────────────────────────────────────

@events_bp.route("/<event_id>/apply", methods=["POST"])
@volunteer_required
def apply_to_event(event_id):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    try:
        oid = ObjectId(event_id)
    except Exception:
        return jsonify({"error": "Invalid event ID"}), 400

    event = db.events.find_one({"_id": oid})
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if event["status"] != "Open":
        return jsonify({"error": "Applications are not open for this event"}), 400

    existing = db.applications.find_one({
        "eventId": oid,
        "volunteerId": ObjectId(g.user_id)
    })
    if existing:
        return jsonify({"error": "You have already applied to this event"}), 409

    now = datetime.now(timezone.utc)
    application = {
        "eventId": oid,
        "volunteerId": ObjectId(g.user_id),
        "status": "Pending",
        "createdAt": now,
        "updatedAt": now,
    }
    result = db.applications.insert_one(application)
    application["_id"] = result.inserted_id
    return jsonify({"application": serialize_application(application)}), 201


# ─── NGO: close applications ─────────────────────────────────────────────────

@events_bp.route("/<event_id>/close-applications", methods=["POST"])
@ngo_required
def close_applications(event_id):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    try:
        oid = ObjectId(event_id)
    except Exception:
        return jsonify({"error": "Invalid event ID"}), 400

    event = db.events.find_one({"_id": oid})
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if str(event["ngoId"]) != g.user_id:
        return jsonify({"error": "Not authorized"}), 403
    if event["status"] != "Open":
        return jsonify({"error": "Can only close applications for Open events"}), 400

    now = datetime.now(timezone.utc)
    db.events.update_one({"_id": oid}, {"$set": {"status": "Applications Closed", "updatedAt": now}})
    event["status"] = "Applications Closed"
    event["updatedAt"] = now
    return jsonify({"event": serialize_event(event)})


# ─── NGO: complete event ──────────────────────────────────────────────────────

@events_bp.route("/<event_id>/complete", methods=["POST"])
@ngo_required
def complete_event(event_id):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    try:
        oid = ObjectId(event_id)
    except Exception:
        return jsonify({"error": "Invalid event ID"}), 400

    event = db.events.find_one({"_id": oid})
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if str(event["ngoId"]) != g.user_id:
        return jsonify({"error": "Not authorized"}), 403
    if event["status"] != "Applications Closed":
        return jsonify({"error": "Can only complete events with status 'Applications Closed'"}), 400

    now = datetime.now(timezone.utc)
    db.events.update_one({"_id": oid}, {"$set": {"status": "Completed", "updatedAt": now}})
    event["status"] = "Completed"
    event["updatedAt"] = now
    return jsonify({"event": serialize_event(event)})


# ─── NGO: rate accepted volunteer ────────────────────────────────────────────

@events_bp.route("/<event_id>/rate", methods=["POST"])
@ngo_required
def rate_volunteer(event_id):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    try:
        oid = ObjectId(event_id)
    except Exception:
        return jsonify({"error": "Invalid event ID"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    volunteer_id_str = data.get("volunteerId", "")
    rating = data.get("rating")

    if not volunteer_id_str:
        return jsonify({"error": "volunteerId is required"}), 400
    if rating is None or not isinstance(rating, (int, float)) or not (1 <= int(rating) <= 5):
        return jsonify({"error": "rating must be an integer between 1 and 5"}), 400

    rating = int(rating)

    try:
        vol_oid = ObjectId(volunteer_id_str)
    except Exception:
        return jsonify({"error": "Invalid volunteerId"}), 400

    event = db.events.find_one({"_id": oid})
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if str(event["ngoId"]) != g.user_id:
        return jsonify({"error": "Not authorized"}), 403
    if event["status"] != "Completed":
        return jsonify({"error": "Can only rate volunteers for Completed events"}), 400

    accepted = db.applications.find_one({
        "eventId": oid,
        "volunteerId": vol_oid,
        "status": "Accepted",
    })
    if not accepted:
        return jsonify({"error": "Volunteer was not accepted for this event"}), 400

    existing_rating = db.ratings.find_one({
        "eventId": oid,
        "volunteerId": vol_oid,
        "ngoId": ObjectId(g.user_id),
    })
    if existing_rating:
        return jsonify({"error": "You have already rated this volunteer for this event"}), 409

    now = datetime.now(timezone.utc)
    db.ratings.insert_one({
        "eventId": oid,
        "volunteerId": vol_oid,
        "ngoId": ObjectId(g.user_id),
        "rating": rating,
        "createdAt": now,
    })

    all_ratings = list(db.ratings.find({"volunteerId": vol_oid}))
    avg = sum(r["rating"] for r in all_ratings) / len(all_ratings)
    db.volunteers.update_one({"_id": vol_oid}, {"$set": {"rating": round(avg, 2)}})

    return jsonify({"message": "Rating submitted", "averageRating": round(avg, 2)}), 201


# ─── NGO: view event applications ────────────────────────────────────────────

@events_bp.route("/<event_id>/applications", methods=["GET"])
@ngo_required
def get_event_applications(event_id):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 503

    try:
        oid = ObjectId(event_id)
    except Exception:
        return jsonify({"error": "Invalid event ID"}), 400

    event = db.events.find_one({"_id": oid})
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if str(event["ngoId"]) != g.user_id:
        return jsonify({"error": "Not authorized"}), 403

    applications = list(db.applications.find({"eventId": oid}))
    vol_ids = [a["volunteerId"] for a in applications]
    volunteers = {v["_id"]: v for v in db.volunteers.find({"_id": {"$in": vol_ids}})}

    rated_vol_ids = set()
    if event["status"] == "Completed":
        ratings = list(db.ratings.find({"eventId": oid, "ngoId": ObjectId(g.user_id)}))
        rated_vol_ids = {str(r["volunteerId"]) for r in ratings}

    result = []
    for app in applications:
        vol = volunteers.get(app["volunteerId"])
        serialized = serialize_application(app, volunteer=vol)
        serialized["rated"] = str(app["volunteerId"]) in rated_vol_ids
        result.append(serialized)

    return jsonify({"applications": result})
