"""Hybrid risk scoring: rules (explainable) + ML model (pattern learning).

Every rule adds points AND a plain-English reason. The ML probability is blended
in so the final score benefits from both.
"""
import time
from collections import defaultdict

import ml
from simulator import USERS

_recent = defaultdict(list)  # user -> timestamps of recent transactions

# --- Tune these weights if you like -----------------------------------
W_AMOUNT_HIGH = 35   # amount >= 5x user's usual
W_AMOUNT_MID = 15    # amount 3x-5x user's usual
W_ODD_HOUR = 20      # between 12 AM and 5 AM
W_NEW_PAYEE = 20     # first time paying this payee
W_LOCATION = 15      # not in the user's home city
W_VELOCITY = 30      # 3+ transfers within 2 minutes
VELOCITY_WINDOW = 120  # seconds
RULE_WEIGHT = 0.6    # final = RULE_WEIGHT * rules + (1 - RULE_WEIGHT) * ML
# ----------------------------------------------------------------------


def level_for(score):
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def score_txn(txn, record=True):
    """Score one transaction.

    record=False scores without adding to the user's velocity history, which is
    what the manual "Check a transaction" form uses.
    """
    info = USERS[txn["user"]]
    avg, home = info["avg"], info["home"]
    points, reasons, codes = 0, [], []

    ratio = txn["amount"] / avg
    if ratio >= 5:
        points += W_AMOUNT_HIGH
        reasons.append(
            f"Amount ₹{txn['amount']:,} is {ratio:.0f}x {txn['user']}'s usual spend (₹{avg:,})."
        )
        codes.append({"c": "amount", "ratio": f"{ratio:.0f}"})
    elif ratio >= 3:
        points += W_AMOUNT_MID
        reasons.append(
            f"Amount ₹{txn['amount']:,} is {ratio:.1f}x {txn['user']}'s usual spend (₹{avg:,})."
        )
        codes.append({"c": "amount", "ratio": f"{ratio:.1f}"})

    if 0 <= txn["hour"] <= 5:
        points += W_ODD_HOUR
        reasons.append(f"Made at an unusual hour ({txn['hour']}:00 AM).")
        codes.append({"c": "odd_hour"})

    if txn["new_payee"]:
        points += W_NEW_PAYEE
        reasons.append(f"First-ever payment to {txn['payee']}.")
        codes.append({"c": "new_payee"})

    if txn["location"] != home:
        points += W_LOCATION
        reasons.append(
            f"Made from {txn['location']}, but {txn['user']} usually transacts from {home}."
        )
        codes.append({"c": "location"})

    now = time.time()
    history = [t for t in _recent[txn["user"]] if now - t < VELOCITY_WINDOW]
    if record:
        history.append(now)
        _recent[txn["user"]] = history
        count = len(history)
    else:
        count = len(history) + 1
    if count >= 3:
        points += W_VELOCITY
        reasons.append(f"{count} transfers in the last 2 minutes.")
        codes.append({"c": "velocity", "count": count})

    rule_score = min(points, 100)

    # ML layer
    ml_prob = ml.fraud_probability(txn, recent_count=count)
    ml_score = round(ml_prob * 100)
    final = round(RULE_WEIGHT * rule_score + (1 - RULE_WEIGHT) * ml_score)

    if not reasons:
        reasons.append("Matches this user's normal behaviour.")
        codes.append({"c": "normal"})
    reasons.append(f"ML model estimates a {ml_score}% chance this is fraud.")
    codes.append({"c": "ml", "pct": ml_score})

    result = dict(txn)
    result.update({
        "score": final,
        "rule_score": rule_score,
        "ml_score": ml_score,
        "level": level_for(final),
        "reasons": reasons,
        "codes": codes,      # structured reasons, translated by the dashboard
        "avg": avg,
        "home": home,
    })
    return result


if __name__ == "__main__":
    from simulator import normal_txn, fraud_demo
    print(score_txn(normal_txn()))
    print(score_txn(fraud_demo()[0]))
