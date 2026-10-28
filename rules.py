"""Rule-based risk scoring. Every rule adds points AND a plain-English reason."""
import time
from collections import defaultdict
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
# ----------------------------------------------------------------------


def level_for(score):
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def score_txn(txn):
    info = USERS[txn["user"]]
    avg, home = info["avg"], info["home"]
    points, reasons = 0, []

    ratio = txn["amount"] / avg
    if ratio >= 5:
        points += W_AMOUNT_HIGH
        reasons.append(
            f"Amount ₹{txn['amount']:,} is {ratio:.0f}x {txn['user']}'s usual spend (₹{avg:,})."
        )
    elif ratio >= 3:
        points += W_AMOUNT_MID
        reasons.append(
            f"Amount ₹{txn['amount']:,} is {ratio:.1f}x {txn['user']}'s usual spend (₹{avg:,})."
        )

    if 0 <= txn["hour"] <= 5:
        points += W_ODD_HOUR
        reasons.append(f"Made at an unusual hour ({txn['hour']}:00 AM).")

    if txn["new_payee"]:
        points += W_NEW_PAYEE
        reasons.append(f"First-ever payment to {txn['payee']}.")

    if txn["location"] != home:
        points += W_LOCATION
        reasons.append(
            f"Made from {txn['location']}, but {txn['user']} usually transacts from {home}."
        )

    now = time.time()
    _recent[txn["user"]] = [t for t in _recent[txn["user"]] if now - t < VELOCITY_WINDOW]
    _recent[txn["user"]].append(now)
    count = len(_recent[txn["user"]])
    if count >= 3:
        points += W_VELOCITY
        reasons.append(f"{count} transfers in the last 2 minutes.")

    points = min(points, 100)
    if not reasons:
        reasons.append("Matches this user's normal behaviour.")

    result = dict(txn)
    result.update({"score": points, "level": level_for(points), "reasons": reasons})
    return result


if __name__ == "__main__":
    from simulator import normal_txn, fraud_demo
    print(score_txn(normal_txn()))
    print(score_txn(fraud_demo()[0]))
