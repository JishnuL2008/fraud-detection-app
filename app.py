import json
import time
from collections import deque
from datetime import datetime

from flask import Flask, Response, jsonify, request, send_from_directory

import ml
import simulator
from rules import score_txn

app = Flask(__name__, static_folder="static")
pending = deque()  # scripted demo transactions waiting to be streamed
actions = {}       # transaction id -> {"action": ..., "time": ...}

ml.train()  # train the model once at startup

VALID_ACTIONS = {"alert", "block", "safe"}
ACTION_LABELS = {"alert": "Alert sent", "block": "Blocked", "safe": "Marked safe"}


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/users")
def users():
    """User profiles + locations, used to fill the 'Check a transaction' form."""
    return jsonify(
        users=simulator.USERS,
        locations=sorted({u["home"] for u in simulator.USERS.values()} | {"Delhi", "Kolkata", "Mumbai"}),
    )


@app.route("/stream")
def stream():
    def generate():
        while True:
            if pending:
                txn = pending.popleft()
                delay = 0.5
            else:
                txn = simulator.next_txn()
                delay = 1.3
            yield f"data: {json.dumps(score_txn(txn))}\n\n"
            time.sleep(delay)

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/check", methods=["POST"])
def check():
    """Score a manually entered transaction (does not affect the live stream)."""
    data = request.get_json(silent=True) or {}
    try:
        user = data["user"]
        if user not in simulator.USERS:
            return jsonify(error="Unknown user"), 400
        amount = int(data["amount"])
        hour = int(data["hour"])
        if amount <= 0 or not 0 <= hour <= 23:
            raise ValueError
        new_payee = bool(data.get("new_payee", False))
        txn = {
            "id": 0,
            "user": user,
            "amount": amount,
            "payee": "a new payee" if new_payee else "a known payee",
            "new_payee": new_payee,
            "hour": hour,
            "location": str(data.get("location", simulator.USERS[user]["home"]))[:40],
        }
    except (KeyError, TypeError, ValueError):
        return jsonify(error="Please enter a valid user, amount (>0) and hour (0-23)."), 400
    return jsonify(score_txn(txn, record=False))


@app.route("/action", methods=["POST"])
def action():
    """Record what an analyst did about a flagged transaction."""
    data = request.get_json(silent=True) or {}
    act, txn_id = data.get("action"), data.get("id")
    if act not in VALID_ACTIONS or not isinstance(txn_id, int):
        return jsonify(error="Invalid action"), 400
    actions[txn_id] = {"action": act, "label": ACTION_LABELS[act],
                       "time": datetime.now().strftime("%H:%M:%S")}
    print(f"[{actions[txn_id]['time']}] Transaction #{txn_id}: {ACTION_LABELS[act]}")
    return jsonify(ok=True, **actions[txn_id])


@app.route("/actions")
def list_actions():
    return jsonify(actions)


@app.route("/trigger/fraud", methods=["POST"])
def trigger_fraud():
    pending.extend(simulator.fraud_demo())
    return jsonify(ok=True)


@app.route("/trigger/burst", methods=["POST"])
def trigger_burst():
    pending.extend(simulator.burst_demo())
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(debug=False, threaded=True, port=5000)
