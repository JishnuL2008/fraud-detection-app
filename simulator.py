"""Generates synthetic UPI-style transactions (all data is fake)."""
import random
import itertools

# Each user has a typical spend (avg, in rupees) and a home city.
USERS = {
    "Ramesh":  {"avg": 1500, "home": "Mysuru"},
    "Lakshmi": {"avg": 800,  "home": "Bengaluru"},
    "Arjun":   {"avg": 2500, "home": "Bengaluru"},
    "Meena":   {"avg": 1200, "home": "Hubballi"},
    "Suresh":  {"avg": 3000, "home": "Mangaluru"},
    "Kavya":   {"avg": 2000, "home": "Bengaluru"},
    "Imran":   {"avg": 1800, "home": "Chennai"},
    "Divya":   {"avg": 1000, "home": "Mysuru"},
}

KNOWN_PAYEES = [
    "Grocery Store", "Electricity Board", "Mobile Recharge",
    "Milk Vendor", "Family Member", "Medical Shop",
]

_ids = itertools.count(1)
_payee_ids = itertools.count(1)


def _new_payee_name():
    return f"Unknown_Payee_{next(_payee_ids)}"


def normal_txn():
    user = random.choice(list(USERS))
    info = USERS[user]
    amount = int(round(info["avg"] * random.uniform(0.4, 1.4) / 10) * 10)
    is_new = random.random() < 0.08
    return {
        "id": next(_ids),
        "user": user,
        "amount": amount,
        "payee": _new_payee_name() if is_new else random.choice(KNOWN_PAYEES),
        "new_payee": is_new,
        "hour": random.randint(8, 21),
        "location": info["home"] if random.random() > 0.03 else "Delhi",
    }


def suspicious_txn():
    """Randomly injected fraud-like transaction."""
    user = random.choice(list(USERS))
    info = USERS[user]
    return {
        "id": next(_ids),
        "user": user,
        "amount": int(info["avg"] * random.uniform(5, 12)),
        "payee": _new_payee_name(),
        "new_payee": True,
        "hour": random.choice([0, 1, 2, 3, 4]),
        "location": random.choice([info["home"], "Delhi", "Kolkata"]),
    }


def fraud_demo():
    """Scripted demo: a senior's account sends a large amount at 3 AM."""
    return [{
        "id": next(_ids),
        "user": "Ramesh",
        "amount": 24000,
        "payee": _new_payee_name(),
        "new_payee": True,
        "hour": 3,
        "location": "Delhi",
    }]


def burst_demo():
    """Scripted demo: 4 rapid transfers to different new payees."""
    return [{
        "id": next(_ids),
        "user": "Lakshmi",
        "amount": 4900,
        "payee": _new_payee_name(),
        "new_payee": True,
        "hour": 14,
        "location": "Bengaluru",
    } for _ in range(4)]


def next_txn():
    """Mostly normal, occasionally suspicious."""
    return suspicious_txn() if random.random() < 0.08 else normal_txn()
