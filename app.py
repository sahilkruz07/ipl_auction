"""IPL 2027 Auction Prediction Game - Flask + MongoDB backend."""
import functools
import hmac
import math
import os
import secrets
import uuid
from datetime import timedelta

from flask import (Flask, abort, g, jsonify, redirect, render_template,
                   request, session, url_for)
from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError
from werkzeug.security import check_password_hash, generate_password_hash

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
MONGO_URI = os.environ.get("MONGO_URI", "")
UNSOLD = "UNSOLD"
ROLES = ("batter", "bowler", "allrounder", "wicket keeper")
USER_ROLES = ("player", "admin")
EXACT_EPSILON = 1e-6
MAX_AMOUNT = 100.0  # Crores; sanity cap on any single amount

DEFAULT_RULES = {
    "team_match_points": 12,
    "amount_tiers": [
        {"min_accuracy": 1.00, "max_accuracy": 1.00, "points": 15},
        {"min_accuracy": 0.90, "max_accuracy": 0.999999, "points": 9},
        {"min_accuracy": 0.80, "max_accuracy": 0.899999, "points": 4},
        {"min_accuracy": 0.70, "max_accuracy": 0.799999, "points": 1},
    ],
    "default_amount_points": 0,
}

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client.get_default_database(default="ipl_auction_game")

app = Flask(__name__)
_secret = os.environ.get("SECRET_KEY")
if not _secret:
    _secret = secrets.token_hex(32)
    print("WARNING: SECRET_KEY not set; using a random key. "
          "Sessions will reset on restart and break with multiple workers.")
app.config.update(
    SECRET_KEY=_secret,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    MAX_CONTENT_LENGTH=64 * 1024,
    TEMPLATES_AUTO_RELOAD=True,
)


def asset(filename):
    """Static URL with an mtime version so browsers never use a stale CSS/JS file."""
    try:
        v = int(os.path.getmtime(os.path.join(app.static_folder, filename)))
    except OSError:
        v = 0
    return url_for("static", filename=filename, v=v)


app.jinja_env.globals["asset"] = asset


def ensure_indexes():
    db.users.create_index([("username", ASCENDING)], unique=True)
    db.users.create_index([("user_id", ASCENDING)], unique=True)
    db.playerList.create_index([("player_id", ASCENDING)], unique=True)
    db.teamData.create_index([("team_name", ASCENDING)], unique=True)
    db.config.create_index([("key", ASCENDING)], unique=True)
    db.betTable.create_index([("user_id", ASCENDING), ("player_id", ASCENDING)], unique=True)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def r2(v):
    return round(float(v) + 0.0, 2)


def parse_amount(raw):
    """Parse a currency amount; raises ValueError on anything non-finite/invalid."""
    if raw is None or isinstance(raw, bool) or (isinstance(raw, str) and not raw.strip()):
        raise ValueError("Amount is required")
    v = float(raw)
    if not math.isfinite(v):
        raise ValueError("Amount must be a finite number")
    if v < 0 or v > MAX_AMOUNT:
        raise ValueError(f"Amount must be between 0 and {MAX_AMOUNT:g} Cr")
    return r2(v)


def get_config(key, default=None):
    doc = db.config.find_one({"key": key})
    return doc["value"] if doc else default


def is_locked():
    return bool(get_config("edit_cutoff_flag", False))


def pid_sort_key(p):
    pid = str(p["player_id"])
    return (0, int(pid), "") if pid.isdigit() else (1, 0, pid)


def all_teams():
    return list(db.teamData.find({}, {"_id": 0}).sort("purse_left", -1))


def all_players():
    return sorted(db.playerList.find({}, {"_id": 0}), key=pid_sort_key)


def wants_json():
    return request.path.startswith("/api/")


# --------------------------------------------------------------------------
# Auth, CSRF, decorators
# --------------------------------------------------------------------------
_DUMMY_HASH = generate_password_hash("not-a-real-password")


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def load_user_and_check_csrf():
    g.user = None
    uid = session.get("user_id")
    if uid:
        g.user = db.users.find_one({"user_id": uid}, {"_id": 0, "password": 0})
        # A password change rotates session_ver, which signs out every other session.
        if not g.user or g.user.get("session_ver", "") != session.get("ver", ""):
            g.user = None
            session.clear()
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        sent = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token", "")
        expected = session.get("csrf", "")
        if not expected or not hmac.compare_digest(str(sent), expected):
            if wants_json():
                return jsonify(error="Invalid or missing CSRF token. Reload the page."), 400
            abort(400)


@app.after_request
def security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "same-origin")
    return resp


def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*a, **kw):
        if not g.user:
            if wants_json():
                return jsonify(error="Authentication required"), 401
            return redirect(url_for("login"))
        return fn(*a, **kw)
    return wrapper


def admin_required(fn):
    @functools.wraps(fn)
    @login_required
    def wrapper(*a, **kw):
        if g.user["role"] != "admin":
            if wants_json():
                return jsonify(error="Admin access required"), 403
            abort(403)
        return fn(*a, **kw)
    return wrapper


@app.context_processor
def inject_globals():
    return {"user": g.get("user"), "locked": is_locked() if g.get("user") else False}


@app.get("/")
def index():
    if not g.user:
        return redirect(url_for("login"))
    return redirect(url_for("admin_page" if g.user["role"] == "admin" else "bets_page"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip().lower()
        password = request.form.get("password") or ""
        u = db.users.find_one({"username": username})
        ok = check_password_hash(u["password"] if u else _DUMMY_HASH, password)
        if u and ok:
            session.clear()
            session.permanent = True
            session["user_id"] = u["user_id"]
            session["ver"] = u.get("session_ver", "")
            return redirect(url_for("index"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)


@app.get("/account")
@login_required
def account_page():
    return render_template("account.html")


@app.post("/api/account/password")
@login_required
def api_change_password():
    d = request.get_json(silent=True) or {}
    current = str(d.get("current_password", ""))
    new = str(d.get("new_password", ""))
    u = db.users.find_one({"user_id": g.user["user_id"]})
    if not check_password_hash(u["password"], current):
        return jsonify(error="Current password is incorrect"), 400
    if not (8 <= len(new) <= 128):
        return jsonify(error="New password must be 8-128 characters"), 400
    if new == current:
        return jsonify(error="New password must be different from the current one"), 400
    ver = secrets.token_hex(8)
    db.users.update_one({"user_id": u["user_id"]},
                        {"$set": {"password": generate_password_hash(new), "session_ver": ver}})
    session["ver"] = ver  # keep this session signed in
    return jsonify(ok=True)


@app.post("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))



# --------------------------------------------------------------------------
# Scoring engine
# --------------------------------------------------------------------------
def amount_points(bet, actual, rules):
    """Returns (points, is_exact)."""
    bet, actual = float(bet), float(actual)
    if abs(bet - actual) < EXACT_EPSILON:
        accuracy, exact = 1.0, True
    else:
        exact = False
        if actual <= 0:
            accuracy = 0.0  # actual == 0 and bet > 0
        else:
            accuracy = max(0.0, 1.0 - abs(bet - actual) / actual)
    for tier in sorted(rules["amount_tiers"], key=lambda t: -t["min_accuracy"]):
        floor = tier["min_accuracy"]
        tol = 1e-9 if floor < 1.0 else 0.0  # absorb float noise except for the exact tier
        if accuracy + tol >= floor:
            return tier["points"], exact
    return rules.get("default_amount_points", 0), exact


def score_bet(bet_team, bet_amount, sold_to, sold_price, rules):
    team_hit = bet_team == sold_to
    team_pts = rules["team_match_points"] if team_hit else 0
    amt_pts, exact = amount_points(bet_amount, sold_price or 0.0, rules)
    return {"team_points": team_pts, "amount_points": amt_pts,
            "points": team_pts + amt_pts, "team_hit": team_hit, "exact_hit": exact}


def compute_reveal():
    rules = get_config("scoring_rules", DEFAULT_RULES)
    users = sorted(db.users.find({"role": "player"}, {"_id": 0, "password": 0}),
                   key=lambda u: u["displayname"].lower())
    players = all_players()
    bets = {(b["user_id"], b["player_id"]): b for b in db.betTable.find({}, {"_id": 0})}
    stats = {u["user_id"]: {"user_id": u["user_id"], "displayname": u["displayname"],
                            "total_points": 0, "team_hits": 0, "exact_hits": 0, "scored": 0}
             for u in users}
    rows = []
    for p in players:
        sold = p.get("sold_to") is not None
        preds = {}
        for u in users:
            b = bets.get((u["user_id"], p["player_id"]))
            if not b:
                preds[u["user_id"]] = None
                continue
            entry = {"bet_team": b["bet_team"], "bet_amount": r2(b["bet_amount"]), "points": None}
            if sold:
                s = score_bet(b["bet_team"], b["bet_amount"], p["sold_to"], p.get("sold_price"), rules)
                entry.update(points=s["points"], team_points=s["team_points"],
                             amount_points=s["amount_points"])
                st = stats[u["user_id"]]
                st["total_points"] += s["points"]
                st["team_hits"] += int(s["team_hit"])
                st["exact_hits"] += int(s["exact_hit"])
                st["scored"] += 1
            preds[u["user_id"]] = entry
        rows.append({**p, "predictions": preds})
    board = sorted(stats.values(), key=lambda s: (-s["total_points"], -s["team_hits"],
                                                   -s["exact_hits"], s["displayname"].lower()))
    prev, rank = None, 0
    for i, s in enumerate(board, 1):
        key = (s["total_points"], s["team_hits"], s["exact_hits"])
        if key != prev:
            rank = i
        s["rank"], prev = rank, key
    return {"users": [{"user_id": u["user_id"], "displayname": u["displayname"]} for u in users],
            "players": rows, "leaderboard": board,
            "sold_count": sum(1 for p in players if p.get("sold_to") is not None)}


# --------------------------------------------------------------------------
# Bet validation
# --------------------------------------------------------------------------
def team_usage(user_id, exclude_player_id=None):
    players = {p["player_id"]: p for p in db.playerList.find({}, {"_id": 0})}
    usage = {}
    for b in db.betTable.find({"user_id": user_id}, {"_id": 0}):
        if b["player_id"] == exclude_player_id or b["bet_team"] == UNSOLD:
            continue
        u = usage.setdefault(b["bet_team"], {"spent": 0.0, "count": 0, "overseas": 0})
        u["spent"] += b["bet_amount"]
        u["count"] += 1
        if players.get(b["player_id"], {}).get("is_overseas"):
            u["overseas"] += 1
    return usage


def validate_bet(user_id, player, team_code, amount):
    """Returns (error_message|None, offending_team|None). Excludes the user's previous bet on this player."""
    if team_code == UNSOLD:
        return None, None
    team = db.teamData.find_one({"team_name": team_code})
    if not team:
        return f"Invalid team '{team_code}'", None
    if amount <= 0:
        return "Amount must be greater than 0", team_code
    u = team_usage(user_id, exclude_player_id=player["player_id"]).get(
        team_code, {"spent": 0.0, "count": 0, "overseas": 0})
    purse_left = r2(team["purse_left"] - u["spent"])
    if r2(purse_left - amount) < 0:
        return f"Exceeds {team_code} remaining purse of ₹{purse_left:.2f} Cr", team_code
    if team["available_slots"] - u["count"] - 1 < 0:
        return (f"Cannot assign to {team_code}: Total slots limit "
                f"({u['count']}/{team['available_slots']}) already reached"), team_code
    if player.get("is_overseas") and team["overseas_slots"] - u["overseas"] - 1 < 0:
        return (f"Cannot assign to {team_code}: Overseas limit "
                f"({u['overseas']}/{team['overseas_slots']}) already reached"), team_code
    return None, None


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
@app.get("/bets")
@login_required
def bets_page():
    if g.user["role"] == "admin":
        return redirect(url_for("admin_page"))
    return render_template("bets.html")


@app.get("/reveal")
@login_required
def reveal_page():
    return render_template("reveal.html")


@app.get("/leaderboard")
@login_required
def leaderboard_page():
    return render_template("leaderboard.html")


@app.get("/admin")
@admin_required
def admin_page():
    return render_template("admin.html", teams=all_teams(), players=all_players(),
                           users=list(db.users.find({}, {"_id": 0, "password": 0}).sort("username", 1)),
                           roles=ROLES, user_roles=USER_ROLES)


# --------------------------------------------------------------------------
# Player API
# --------------------------------------------------------------------------
@app.get("/api/state")
@login_required
def api_state():
    bets = {b["player_id"]: b for b in db.betTable.find({"user_id": g.user["user_id"]}, {"_id": 0})}
    players = []
    for p in all_players():
        b = bets.get(p["player_id"])
        players.append({**p, "bet": {"bet_team": b["bet_team"], "bet_amount": r2(b["bet_amount"])} if b else None})
    return jsonify(locked=is_locked(), teams=all_teams(), players=players)


@app.post("/api/bets")
@login_required
def api_save_bet():
    if g.user["role"] != "player":
        return jsonify(error="Only players can place bets"), 403
    if is_locked():
        return jsonify(error="Betting is locked. The auction has started."), 403
    data = request.get_json(silent=True) or {}
    player = db.playerList.find_one({"player_id": str(data.get("player_id", ""))}, {"_id": 0})
    if not player:
        return jsonify(error="Player not found"), 404
    team_code = str(data.get("bet_team", "")).strip().upper()
    if not team_code:
        return jsonify(error="Select a team"), 400
    if team_code == UNSOLD:
        amount = 0.0
    else:
        try:
            amount = parse_amount(data.get("bet_amount"))
        except (ValueError, TypeError) as e:
            return jsonify(error=str(e) if str(e) else "Invalid amount", team=team_code), 400
    err, bad_team = validate_bet(g.user["user_id"], player, team_code, amount)
    if err:
        return jsonify(error=err, team=bad_team), 400
    db.betTable.update_one({"user_id": g.user["user_id"], "player_id": player["player_id"]},
                           {"$set": {"bet_team": team_code, "bet_amount": amount}}, upsert=True)
    return jsonify(ok=True, bet={"bet_team": team_code, "bet_amount": amount})


@app.delete("/api/bets/<player_id>")
@login_required
def api_delete_bet(player_id):
    if g.user["role"] != "player":
        return jsonify(error="Only players can place bets"), 403
    if is_locked():
        return jsonify(error="Betting is locked. The auction has started."), 403
    db.betTable.delete_one({"user_id": g.user["user_id"], "player_id": player_id})
    return jsonify(ok=True)


@app.get("/api/reveal")
@login_required
def api_reveal():
    if not is_locked():
        return jsonify(error="Bets stay hidden until the auction starts."), 403
    return jsonify(compute_reveal())


# --------------------------------------------------------------------------
# Admin API
# --------------------------------------------------------------------------
@app.post("/api/admin/cutoff")
@admin_required
def api_cutoff():
    data = request.get_json(silent=True) or {}
    value = data.get("value")
    new = (not is_locked()) if value is None else bool(value)
    db.config.update_one({"key": "edit_cutoff_flag"}, {"$set": {"value": new}}, upsert=True)
    return jsonify(ok=True, edit_cutoff_flag=new)


@app.post("/api/admin/players/<player_id>/result")
@admin_required
def api_player_result(player_id):
    data = request.get_json(silent=True) or {}
    sold_to = data.get("sold_to")
    sold_to = str(sold_to).strip().upper() if sold_to not in (None, "") else None
    if sold_to is None:
        update = {"sold_to": None, "sold_price": None}
    elif sold_to == UNSOLD:
        update = {"sold_to": UNSOLD, "sold_price": 0.0}
    else:
        if not db.teamData.find_one({"team_name": sold_to}):
            return jsonify(error=f"Invalid team '{sold_to}'"), 400
        try:
            price = parse_amount(data.get("sold_price"))
        except (ValueError, TypeError) as e:
            return jsonify(error=str(e) or "Invalid price"), 400
        if price <= 0:
            return jsonify(error="Sold price must be greater than 0 (use UNSOLD otherwise)"), 400
        update = {"sold_to": sold_to, "sold_price": price}
    res = db.playerList.update_one({"player_id": player_id}, {"$set": update})
    if not res.matched_count:
        return jsonify(error="Player not found"), 404
    return jsonify(ok=True, **update)


@app.post("/api/admin/users")
@admin_required
def api_add_user():
    d = request.get_json(silent=True) or {}
    username = str(d.get("username", "")).strip().lower()
    displayname = str(d.get("displayname", "")).strip() or username
    password = str(d.get("password", ""))
    role = d.get("role", "player")
    if not (3 <= len(username) <= 40) or not username.replace("_", "").replace(".", "").isalnum():
        return jsonify(error="Username must be 3-40 chars: letters, digits, '_' or '.'"), 400
    if len(password) < 8:
        return jsonify(error="Password must be at least 8 characters"), 400
    if role not in USER_ROLES:
        return jsonify(error="Invalid role"), 400
    if len(displayname) > 60:
        return jsonify(error="Display name too long"), 400
    try:
        db.users.insert_one({"user_id": str(uuid.uuid4()), "username": username,
                             "password": generate_password_hash(password),
                             "displayname": displayname, "role": role})
    except DuplicateKeyError:
        return jsonify(error="Username already exists"), 409
    return jsonify(ok=True)



@app.post("/api/admin/players")
@admin_required
def api_add_player():
    d = request.get_json(silent=True) or {}
    name = str(d.get("player_name", "")).strip()
    role = d.get("role")
    if not (1 <= len(name) <= 80):
        return jsonify(error="Player name is required (max 80 chars)"), 400
    if role not in ROLES:
        return jsonify(error="Invalid role"), 400
    existing = [pid_sort_key(p) for p in db.playerList.find({}, {"player_id": 1})]
    nums = [k[1] for k in existing if k[0] == 0]
    for _ in range(5):  # retry on a concurrent insert collision
        pid = str((max(nums) if nums else 0) + 1)
        try:
            db.playerList.insert_one({"player_id": pid, "player_name": name,
                                      "is_overseas": bool(d.get("is_overseas")), "role": role,
                                      "sold_to": None, "sold_price": None})
            return jsonify(ok=True, player_id=pid)
        except DuplicateKeyError:
            nums.append(int(pid))
    return jsonify(error="Could not allocate a player id"), 500


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------
@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(413)
def http_error(e):
    if wants_json():
        return jsonify(error=e.description), e.code
    return render_template("error.html", code=e.code, message=e.description), e.code


@app.errorhandler(500)
def server_error(e):
    if wants_json():
        return jsonify(error="Internal server error"), 500
    return render_template("error.html", code=500, message="Something went wrong."), 500


if __name__ == "__main__":
    ensure_indexes()
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 5000)),
            debug=os.environ.get("FLASK_DEBUG", "0") == "1")
