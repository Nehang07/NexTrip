import os
import json
import sqlite3
import secrets
from datetime import datetime, timezone
from flask import Flask, request, jsonify, session, send_from_directory, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nehang.db")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
ASSETS_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path="")


@app.route("/static/<path:filename>")
def static_assets(filename):
    return send_from_directory(ASSETS_DIR, filename)
app.secret_key = os.environ.get("NEHANG_SECRET_KEY", secrets.token_hex(32))
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            loc TEXT NOT NULL,
            country TEXT NOT NULL,
            category TEXT NOT NULL,
            badge TEXT NOT NULL,
            label TEXT NOT NULL,
            rating REAL NOT NULL,
            reviews_count INTEGER NOT NULL DEFAULT 0,
            price_low INTEGER NOT NULL,
            price_high INTEGER NOT NULL,
            flag TEXT NOT NULL,
            season TEXT NOT NULL,
            tags TEXT NOT NULL,
            img TEXT NOT NULL,
            fallback TEXT NOT NULL,
            description TEXT NOT NULL,
            insider_tip TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            destination_id INTEGER NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, destination_id)
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            destination_id INTEGER NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
            rating INTEGER NOT NULL,
            comment TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            destination_name TEXT NOT NULL,
            days INTEGER NOT NULL,
            budget_total INTEGER NOT NULL,
            interests TEXT NOT NULL,
            itinerary_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS budget_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            trip_name TEXT NOT NULL,
            category TEXT NOT NULL,
            label TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    db.commit()

    count = db.execute("SELECT COUNT(*) AS c FROM destinations").fetchone()["c"]
    if count == 0:
        from seed_data import DESTINATIONS
        for d in DESTINATIONS:
            db.execute(
                """INSERT INTO destinations
                   (name, loc, country, category, badge, label, rating, reviews_count,
                    price_low, price_high, flag, season, tags, img, fallback, description, insider_tip)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    d["name"], d["loc"], d["country"], d["category"], d["badge"], d["label"],
                    d["rating"], d["reviews"], d["price_low"], d["price_high"], d["flag"],
                    d["season"], json.dumps(d["tags"]), d["img"], d["fallback"], d["description"],
                    d.get("insider_tip", ""),
                ),
            )
        db.commit()
    db.close()


def row_to_destination(row, fav_ids=None):
    return {
        "id": row["id"],
        "name": row["name"],
        "loc": row["loc"],
        "country": row["country"],
        "category": row["category"],
        "badge": row["badge"],
        "label": row["label"],
        "rating": row["rating"],
        "reviews": row["reviews_count"],
        "price": f"₹{row['price_low']:,}–{row['price_high']:,}",
        "price_low": row["price_low"],
        "price_high": row["price_high"],
        "flag": row["flag"],
        "season": row["season"],
        "tags": json.loads(row["tags"]),
        "img": row["img"],
        "fallback": row["fallback"],
        "description": row["description"],
        "insider_tip": row["insider_tip"],
        "saved": bool(fav_ids and row["id"] in fav_ids),
    }


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    db = get_db()
    return db.execute("SELECT id, name, email FROM users WHERE id=?", (uid,)).fetchone()


def login_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Login required"}), 401
        return fn(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# Static page routes
# ---------------------------------------------------------------------------

@app.route("/")
def home_page():
    return send_from_directory(PUBLIC_DIR, "index.html")


@app.route("/<page>.html")
def page(page):
    filename = f"{page}.html"
    if os.path.exists(os.path.join(PUBLIC_DIR, filename)):
        return send_from_directory(PUBLIC_DIR, filename)
    return jsonify({"error": "Not found"}), 404


# ---------------------------------------------------------------------------
# Auth API
# ---------------------------------------------------------------------------

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        return jsonify({"error": "An account with that email already exists"}), 409

    cur = db.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?,?,?,?)",
        (name, email, generate_password_hash(password), datetime.now(timezone.utc).isoformat()),
    )
    db.commit()
    session["user_id"] = cur.lastrowid
    return jsonify({"id": cur.lastrowid, "name": name, "email": email})


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = user["id"]
    return jsonify({"id": user["id"], "name": user["name"], "email": user["email"]})


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/auth/me")
def me():
    user = current_user()
    if not user:
        return jsonify({"user": None})
    return jsonify({"user": {"id": user["id"], "name": user["name"], "email": user["email"]}})


# ---------------------------------------------------------------------------
# Destinations API
# ---------------------------------------------------------------------------

@app.route("/api/destinations")
def list_destinations():
    db = get_db()
    q = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "all")
    country = request.args.get("country", "")
    sort = request.args.get("sort", "popular")
    max_budget = request.args.get("max_budget", type=int)

    sql = "SELECT * FROM destinations WHERE 1=1"
    params = []
    if category and category != "all":
        sql += " AND category=?"
        params.append(category)
    if country:
        sql += " AND country=?"
        params.append(country)
    if max_budget:
        sql += " AND price_low<=?"
        params.append(max_budget)
    if q:
        sql += " AND (LOWER(name) LIKE ? OR LOWER(loc) LIKE ? OR LOWER(tags) LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like])

    rows = db.execute(sql, params).fetchall()

    if sort == "rating":
        rows = sorted(rows, key=lambda r: r["rating"], reverse=True)
    elif sort == "price-low":
        rows = sorted(rows, key=lambda r: r["price_low"])
    elif sort == "price-high":
        rows = sorted(rows, key=lambda r: r["price_high"], reverse=True)
    elif sort == "hidden":
        rows = sorted(rows, key=lambda r: 0 if r["category"] == "hidden" else 1)
    else:
        rows = sorted(rows, key=lambda r: r["reviews_count"], reverse=True)

    user = current_user()
    fav_ids = set()
    if user:
        fav_ids = {
            r["destination_id"]
            for r in db.execute("SELECT destination_id FROM favorites WHERE user_id=?", (user["id"],)).fetchall()
        }

    return jsonify({
        "total": db.execute("SELECT COUNT(*) c FROM destinations").fetchone()["c"],
        "count": len(rows),
        "results": [row_to_destination(r, fav_ids) for r in rows],
    })


@app.route("/api/destinations/<int:dest_id>")
def get_destination(dest_id):
    db = get_db()
    row = db.execute("SELECT * FROM destinations WHERE id=?", (dest_id,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    user = current_user()
    fav_ids = set()
    if user:
        fav_ids = {
            r["destination_id"]
            for r in db.execute("SELECT destination_id FROM favorites WHERE user_id=?", (user["id"],)).fetchall()
        }
    return jsonify(row_to_destination(row, fav_ids))


@app.route("/api/countries")
def list_countries():
    from seed_data import COUNTRIES
    db = get_db()
    out = []
    for c in COUNTRIES:
        cnt = db.execute("SELECT COUNT(*) n FROM destinations WHERE country=?", (c["name"],)).fetchone()["n"]
        out.append({**c, "count": cnt})
    return jsonify(out)


# ---------------------------------------------------------------------------
# Favorites API
# ---------------------------------------------------------------------------

@app.route("/api/favorites", methods=["GET"])
@login_required
def get_favorites():
    db = get_db()
    uid = session["user_id"]
    rows = db.execute(
        """SELECT d.* FROM destinations d
           JOIN favorites f ON f.destination_id = d.id
           WHERE f.user_id=?""",
        (uid,),
    ).fetchall()
    fav_ids = {r["id"] for r in rows}
    return jsonify([row_to_destination(r, fav_ids) for r in rows])


@app.route("/api/favorites/<int:dest_id>", methods=["POST"])
@login_required
def toggle_favorite(dest_id):
    db = get_db()
    uid = session["user_id"]
    existing = db.execute(
        "SELECT id FROM favorites WHERE user_id=? AND destination_id=?", (uid, dest_id)
    ).fetchone()
    if existing:
        db.execute("DELETE FROM favorites WHERE id=?", (existing["id"],))
        db.commit()
        return jsonify({"saved": False})
    db.execute(
        "INSERT INTO favorites (user_id, destination_id, created_at) VALUES (?,?,?)",
        (uid, dest_id, datetime.now(timezone.utc).isoformat()),
    )
    db.commit()
    return jsonify({"saved": True})


# ---------------------------------------------------------------------------
# Reviews API
# ---------------------------------------------------------------------------

@app.route("/api/reviews")
def list_reviews():
    db = get_db()
    dest_id = request.args.get("destination_id", type=int)
    sql = """SELECT r.*, u.name AS user_name, d.name AS destination_name
              FROM reviews r
              JOIN users u ON u.id = r.user_id
              JOIN destinations d ON d.id = r.destination_id"""
    params = []
    if dest_id:
        sql += " WHERE r.destination_id=?"
        params.append(dest_id)
    sql += " ORDER BY r.created_at DESC"
    rows = db.execute(sql, params).fetchall()
    return jsonify([
        {
            "id": r["id"], "rating": r["rating"], "comment": r["comment"],
            "created_at": r["created_at"], "user_name": r["user_name"],
            "destination_id": r["destination_id"], "destination_name": r["destination_name"],
        }
        for r in rows
    ])


@app.route("/api/reviews", methods=["POST"])
@login_required
def add_review():
    data = request.get_json(force=True) or {}
    dest_id = data.get("destination_id")
    rating = data.get("rating")
    comment = (data.get("comment") or "").strip()

    if not dest_id or not rating or not comment:
        return jsonify({"error": "destination_id, rating and comment are required"}), 400
    try:
        rating = int(rating)
        assert 1 <= rating <= 5
    except (ValueError, AssertionError):
        return jsonify({"error": "rating must be an integer from 1 to 5"}), 400

    db = get_db()
    dest = db.execute("SELECT id FROM destinations WHERE id=?", (dest_id,)).fetchone()
    if not dest:
        return jsonify({"error": "Destination not found"}), 404

    db.execute(
        "INSERT INTO reviews (user_id, destination_id, rating, comment, created_at) VALUES (?,?,?,?,?)",
        (session["user_id"], dest_id, rating, comment, datetime.now(timezone.utc).isoformat()),
    )
    db.execute("UPDATE destinations SET reviews_count = reviews_count + 1 WHERE id=?", (dest_id,))
    db.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# AI Planner API  (curated, real itineraries — not randomly generated)
# ---------------------------------------------------------------------------

MEAL_NOTE = "Try a local specialty restaurant for dinner — ask your accommodation for their top pick."

LEISURE_DAY = dict(
    title="Leisure Day",
    morning="A free morning — revisit your favorite spot from earlier in the trip, or sleep in",
    afternoon="Explore at your own pace: a local market, a café, or anything you didn't get to yet",
    evening=MEAL_NOTE,
)


def build_itinerary(destination_row, days, budget_total, interests):
    from seed_data import ITINERARIES

    per_day_budget = round(budget_total / max(days, 1))
    curated = ITINERARIES.get(destination_row["name"], [])
    insider_tip = destination_row["insider_tip"] if "insider_tip" in destination_row.keys() else ""

    plan = []
    if curated:
        if days <= len(curated):
            # Shorter trip: use the most essential days first.
            chosen = curated[:days]
        else:
            # Longer trip: use everything curated, then add a hidden-gem day
            # (if there's an insider tip) and leisure days for the rest — never
            # random filler, always something specific and true to the place.
            chosen = list(curated)
            remaining = days - len(chosen)
            if insider_tip and remaining > 0:
                chosen.append(dict(
                    title="Hidden Gem Day",
                    morning=f"Set aside today for something most visitors miss: {insider_tip}",
                    afternoon="Take it slow — this is meant to feel like a local secret, not a checklist",
                    evening=MEAL_NOTE,
                ))
                remaining -= 1
            for _ in range(remaining):
                chosen.append(LEISURE_DAY)

        for i, d in enumerate(chosen, start=1):
            plan.append({
                "day": i,
                "title": f"Day {i} — {d['title']}",
                "morning": d["morning"],
                "afternoon": d["afternoon"],
                "evening": d["evening"],
                "budget_estimate": per_day_budget,
            })
    else:
        # Fallback for any destination without curated content yet.
        for i in range(1, days + 1):
            plan.append({
                "day": i,
                "title": f"Day {i}",
                "morning": f"Explore {destination_row['name']}'s main sights at your own pace",
                "afternoon": "Local food and culture",
                "evening": MEAL_NOTE,
                "budget_estimate": per_day_budget,
            })

    summary = (
        f"A {days}-day itinerary for {destination_row['name']} tailored to "
        f"{', '.join(interests) if interests else 'general sightseeing'}, "
        f"averaging ₹{per_day_budget:,} per day."
    )

    if insider_tip and days >= 2 and not any("Hidden Gem Day" in d["title"] for d in plan):
        plan[-1]["evening"] = plan[-1]["evening"] + f" Insider tip: {insider_tip}"

    return {"summary": summary, "days": plan, "total_budget": budget_total, "insider_tip": insider_tip}


@app.route("/api/planner/generate", methods=["POST"])
def generate_plan():
    data = request.get_json(force=True) or {}
    dest_name = (data.get("destination") or "").strip()
    try:
        days = max(1, min(30, int(data.get("days", 3))))
    except (TypeError, ValueError):
        days = 3
    try:
        budget_total = max(0, int(data.get("budget", 10000)))
    except (TypeError, ValueError):
        budget_total = 10000
    interests = data.get("interests") or []

    db = get_db()
    row = db.execute("SELECT * FROM destinations WHERE LOWER(name)=LOWER(?)", (dest_name,)).fetchone()
    if not row:
        row = db.execute("SELECT * FROM destinations WHERE LOWER(name) LIKE ?", (f"%{dest_name.lower()}%",)).fetchone()
    if not row:
        return jsonify({"error": f"No destination matching '{dest_name}' found. Try one from the Explorer page."}), 404

    itinerary = build_itinerary(row, days, budget_total, interests)

    if session.get("user_id"):
        db.execute(
            """INSERT INTO trips (user_id, destination_name, days, budget_total, interests, itinerary_json, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (session["user_id"], row["name"], days, budget_total, json.dumps(interests),
             json.dumps(itinerary), datetime.now(timezone.utc).isoformat()),
        )
        db.commit()

    return jsonify({"destination": row_to_destination(row), "itinerary": itinerary})


@app.route("/api/trips")
@login_required
def list_trips():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM trips WHERE user_id=? ORDER BY created_at DESC", (session["user_id"],)
    ).fetchall()
    return jsonify([
        {
            "id": r["id"], "destination_name": r["destination_name"], "days": r["days"],
            "budget_total": r["budget_total"], "interests": json.loads(r["interests"]),
            "itinerary": json.loads(r["itinerary_json"]), "created_at": r["created_at"],
        }
        for r in rows
    ])


# ---------------------------------------------------------------------------
# Budget API
# ---------------------------------------------------------------------------

@app.route("/api/budget", methods=["GET"])
@login_required
def list_budget():
    db = get_db()
    trip_name = request.args.get("trip_name")
    sql = "SELECT * FROM budget_entries WHERE user_id=?"
    params = [session["user_id"]]
    if trip_name:
        sql += " AND trip_name=?"
        params.append(trip_name)
    sql += " ORDER BY created_at DESC"
    rows = db.execute(sql, params).fetchall()
    return jsonify([
        {
            "id": r["id"], "trip_name": r["trip_name"], "category": r["category"],
            "label": r["label"], "amount": r["amount"], "created_at": r["created_at"],
        }
        for r in rows
    ])


@app.route("/api/budget", methods=["POST"])
@login_required
def add_budget_entry():
    data = request.get_json(force=True) or {}
    trip_name = (data.get("trip_name") or "My Trip").strip()
    category = (data.get("category") or "other").strip()
    label = (data.get("label") or "").strip()
    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "amount must be a number"}), 400

    if not label or amount <= 0:
        return jsonify({"error": "label and a positive amount are required"}), 400

    db = get_db()
    cur = db.execute(
        "INSERT INTO budget_entries (user_id, trip_name, category, label, amount, created_at) VALUES (?,?,?,?,?,?)",
        (session["user_id"], trip_name, category, label, amount, datetime.now(timezone.utc).isoformat()),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "trip_name": trip_name, "category": category, "label": label, "amount": amount})


@app.route("/api/budget/<int:entry_id>", methods=["DELETE"])
@login_required
def delete_budget_entry(entry_id):
    db = get_db()
    db.execute("DELETE FROM budget_entries WHERE id=? AND user_id=?", (entry_id, session["user_id"]))
    db.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
else:
    init_db()
