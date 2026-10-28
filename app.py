import json
import time
from collections import deque

from flask import Flask, Response, jsonify, send_from_directory

import simulator
from rules import score_txn

app = Flask(__name__, static_folder="static")
pending = deque()  # scripted demo transactions waiting to be streamed


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


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
