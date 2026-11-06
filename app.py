import json
import os
import secrets
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, Response, jsonify, render_template, request

app = Flask(__name__)

# --- Firestore -------------------------------------------------------------
# On Render, set FIREBASE_CREDENTIALS to the full service-account JSON text.
# Locally, you can instead point FIREBASE_CREDENTIALS_FILE to the .json file.
def init_db():
    raw = os.environ.get("FIREBASE_CREDENTIALS")
    path = os.environ.get("FIREBASE_CREDENTIALS_FILE")
    if raw:
        cred = credentials.Certificate(json.loads(raw))
    elif path:
        cred = credentials.Certificate(path)
    else:
        raise RuntimeError("Set FIREBASE_CREDENTIALS (JSON text) or FIREBASE_CREDENTIALS_FILE")
    firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_db()
trades = db.collection("trades")

# --- Simple password protection (your journal is private) -------------------
APP_USER = os.environ.get("APP_USER", "trader")
APP_PASSWORD = os.environ.get("APP_PASSWORD")

@app.before_request
def require_login():
    if not APP_PASSWORD:
        return  # no password set (local dev)
    auth = request.authorization
    ok = (
        auth
        and secrets.compare_digest(auth.username or "", APP_USER)
        and secrets.compare_digest(auth.password or "", APP_PASSWORD)
    )
    if not ok:
        return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="Trading Journal"'})

# --- Helpers ---------------------------------------------------------------
def num(value):
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None

def clean(data):
    side = data.get("side", "Long")
    entry, exit_, size = num(data.get("entry")), num(data.get("exit")), num(data.get("size"))
    pnl = None
    if None not in (entry, exit_, size):
        pnl = round((exit_ - entry) * size * (1 if side == "Long" else -1), 2)
    return {
        "date": data.get("date", ""),
        "symbol": (data.get("symbol") or "").upper().strip(),
        "side": side,
        "setup": (data.get("setup") or "").strip(),
        "entry": entry,
        "exit": exit_,
        "stop": num(data.get("stop")),
        "target": num(data.get("target")),
        "size": size,
        "pnl": pnl,
        "reason": (data.get("reason") or "").strip(),      # why I took the trade
        "emotion": (data.get("emotion") or "").strip(),
        "lesson": (data.get("lesson") or "").strip(),      # review after the trade
    }

# --- Routes ----------------------------------------------------------------
@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/trades")
def list_trades():
    docs = trades.order_by("date", direction=firestore.Query.DESCENDING).stream()
    return jsonify([{**d.to_dict(), "id": d.id} for d in docs])

@app.post("/api/trades")
def create_trade():
    data = clean(request.get_json(force=True))
    if not data["symbol"] or not data["reason"]:
        return jsonify(error="Symbol and reason are required"), 400
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    _, ref = trades.add(data)
    return jsonify({**data, "id": ref.id}), 201

@app.put("/api/trades/<trade_id>")
def update_trade(trade_id):
    data = clean(request.get_json(force=True))
    if not data["symbol"] or not data["reason"]:
        return jsonify(error="Symbol and reason are required"), 400
    trades.document(trade_id).update(data)
    return jsonify({**data, "id": trade_id})

@app.delete("/api/trades/<trade_id>")
def delete_trade(trade_id):
    trades.document(trade_id).delete()
    return "", 204

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
