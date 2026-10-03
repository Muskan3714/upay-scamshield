"""
generate_data_profiles.py — PREVIOUS synthetic dataset (kept for comparison): feature-level "Send Money" data
with customer profiles and injected scam patterns. The current main dataset is the raw log from generate_data.py.

ALL DATA IS SYNTHETIC. No real customer data or PII is used.
Every assumption is documented in README.md -> "Synthetic data assumptions".

Each customer has a stable behavioural profile (usual amount, usual active hours, own devices, home district).
Transfers are generated relative to that profile, so "unusual for THIS customer" is meaningful.

Usage:  python generate_data_profiles.py
Writes: data/previous/transactions.csv, user_profiles.csv, forwarding.csv, wallet_roles_ground_truth.csv
"""
import argparse
import os

import numpy as np
import pandas as pd

FEATURES = [
    "amount",                       # BDT
    "amount_ratio",                 # amount / this customer's usual transfer amount
    "hour",                         # 0-23
    "outside_usual_hours",          # 1 if the hour is outside this customer's usual active window
    "is_new_recipient",             # 1 if the customer never sent to this number before
    "recipient_account_age_days",   # age of the receiving wallet
    "recipient_unique_senders_24h", # distinct senders to the recipient in last 24h
    "user_txns_last_1h",            # customer's transfers in the previous hour
    "device_changed",               # 1 if the device is not one of the customer's known devices
    "new_location",                 # 1 if the district is not the customer's usual district
    "on_active_call",               # 1 if the customer is on a phone call while sending
    "user_tenure_days",             # how long the customer has used the wallet
]

MAX_AMOUNT = 25000  # assumed single send-money cap (BDT)
N_USERS, N_SHOPS, N_MULES, N_RINGS = 8000, 300, 80, 12
DISTRICTS = ["Dhaka", "Chattogram", "Gazipur", "Narayanganj", "Cumilla", "Sylhet", "Rajshahi", "Khulna",
             "Barishal", "Rangpur", "Mymensingh", "Bogura", "Jessore", "Noakhali", "Cox's Bazar", "Tangail"]


def make_profiles(rng):
    start = rng.integers(6, 13, N_USERS)
    n_dev = rng.choice([1, 2], N_USERS, p=[0.7, 0.3])
    return pd.DataFrame({
        "user_id": [f"U{i:05d}" for i in range(N_USERS)],
        "usual_amount": (rng.lognormal(7.0, 0.8, N_USERS) / 10).round() * 10,   # median ~1,100 BDT
        "active_start": start,
        "active_end": np.minimum(start + rng.integers(10, 15, N_USERS), 23),
        "devices": [",".join(f"DEV-{x:04X}" for x in rng.integers(0, 65535, k)) for k in n_dev],
        "home_district": rng.choice(DISTRICTS, N_USERS, p=None),
        "known_recipients": rng.integers(3, 16, N_USERS),
        "user_tenure_days": rng.integers(30, 2500, N_USERS),
    })


def _hours(rng, prof, p_in_window):
    """Hour inside the customer's window with probability p, otherwise any hour (weighted to evenings/night)."""
    n = len(prof)
    inside = rng.integers(prof.active_start.values, prof.active_end.values + 1)
    w = np.array([2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2], float)
    anywhere = rng.choice(24, n, p=w / w.sum())
    return np.where(rng.random(n) < p_in_window, inside, anywhere)


def _base(prof, rng, amount, hour, is_new, rec_age, senders, txns1h, p_dev, p_loc, p_call):
    n = len(prof)
    dev_changed = rng.random(n) < p_dev
    new_loc = rng.random(n) < p_loc
    own_dev = [d.split(",")[rng.integers(0, len(d.split(",")))] for d in prof.devices]
    other = rng.choice(DISTRICTS, n)
    return pd.DataFrame({
        "user_id": prof.user_id.values,
        "amount": amount, "usual": prof.usual_amount.values,
        "hour": hour,
        "is_new_recipient": is_new.astype(int),
        "recipient_account_age_days": rec_age,
        "recipient_unique_senders_24h": senders,
        "user_txns_last_1h": txns1h,
        "device_changed": dev_changed.astype(int),
        "new_location": new_loc.astype(int),
        "on_active_call": (rng.random(n) < p_call).astype(int),
        "user_tenure_days": prof.user_tenure_days.values,
        "device_id": np.where(dev_changed, [f"DEV-{x:04X}" for x in rng.integers(0, 65535, n)], own_dev),
        "district": np.where(new_loc, np.where(other == prof.home_district.values, "Bandarban", other),
                             prof.home_district.values),
    })


def _legit(prof, rng):
    n = len(prof)
    usual = prof.usual_amount.values
    amount = usual * rng.lognormal(0, 0.5, n)
    big = rng.random(n) < 0.03                                   # occasional legit big payments (rent, fees)
    amount = np.where(big, amount * rng.uniform(3, 8, n), amount)
    is_new = rng.random(n) < 0.18                                # people do pay new numbers legitimately
    shop = rng.random(n) < 0.08                                  # shops/tutors legitimately receive from many people
    rec_age = np.where(shop, rng.integers(180, 3000, n),
                       np.where(is_new, rng.integers(3, 3000, n), rng.integers(60, 3000, n)))
    senders = np.where(shop, rng.integers(8, 80, n), rng.poisson(1.5, n))
    df = _base(prof, rng, amount, _hours(rng, prof, 0.92), is_new, rec_age, senders, rng.poisson(0.4, n),
               p_dev=0.02, p_loc=0.04, p_call=0.05)
    return df.assign(is_scam=0, scam_type="none", is_shop=shop.astype(int))


def _social_engineering(prof, rng):
    """Fake prize / 'wrong number, send it back' / relative-in-trouble calls.
    The victim is coached on the phone to send to a fresh mule wallet, usually at a normal time of day."""
    n = len(prof)
    df = _base(prof, rng, prof.usual_amount.values * rng.uniform(1.5, 8, n), _hours(rng, prof, 0.85),
               rng.random(n) < 0.92, rng.integers(1, 90, n), rng.integers(4, 45, n), rng.poisson(0.8, n),
               p_dev=0.03, p_loc=0.05, p_call=0.70)
    return df.assign(is_scam=1, scam_type="social_engineering", is_shop=0)


def _account_takeover(prof, rng):
    """Attacker got the PIN/OTP, logs in on a new device somewhere else and drains the wallet, often at night."""
    n = len(prof)
    night = rng.random(n) < 0.6
    hour = np.where(night, rng.integers(0, 6, n), _hours(rng, prof, 0.9))
    df = _base(prof, rng, prof.usual_amount.values * rng.uniform(3, 15, n), hour,
               rng.random(n) < 0.95, rng.integers(1, 120, n), rng.integers(1, 20, n), rng.integers(1, 7, n),
               p_dev=0.85, p_loc=0.70, p_call=0.10)
    return df.assign(is_scam=1, scam_type="account_takeover", is_shop=0)


def _low_signal_scam(prof, rng):
    """Hard cases that look almost normal, to keep the evaluation honest."""
    df = _legit(prof, rng)
    df["amount"] = df["amount"] * rng.uniform(1.0, 3.0, len(df))
    df["is_new_recipient"] = (rng.random(len(df)) < 0.6).astype(int)
    return df.assign(is_scam=1, scam_type="low_signal", is_shop=0)


def generate(n=60000, scam_rate=0.03, seed=42):
    rng = np.random.default_rng(seed)
    profiles = make_profiles(rng)
    pick = lambda k: profiles.iloc[rng.integers(0, N_USERS, k)].reset_index(drop=True)
    n_scam = int(n * scam_rate)
    n_se, n_ato = int(n_scam * 0.55), int(n_scam * 0.30)
    df = pd.concat([_legit(pick(n - n_scam), rng), _social_engineering(pick(n_se), rng),
                    _account_takeover(pick(n_ato), rng), _low_signal_scam(pick(n_scam - n_se - n_ato), rng)],
                   ignore_index=True)
    # Recipients: legit transfers go to people or shops; scams go to mule wallets (uneven: a few busy mules)
    rec = np.where(df.is_shop == 1, [f"S{x:03d}" for x in rng.integers(0, N_SHOPS, len(df))],
                   [f"R{x:05d}" for x in rng.integers(0, 20000, len(df))])
    mw = 1 / np.arange(1, N_MULES + 1) ** 1.3
    mule_pick = rng.permutation(N_MULES)[rng.choice(N_MULES, len(df), p=mw / mw.sum())]
    df["recipient_id"] = np.where(df.is_scam == 1, [f"M{x:03d}" for x in mule_pick], rec)
    df["amount"] = (df["amount"].clip(10, MAX_AMOUNT) / 10).round() * 10
    df["amount_ratio"] = (df["amount"] / df["usual"]).round(2)
    prof_idx = profiles.set_index("user_id")
    s, e = prof_idx.loc[df.user_id, "active_start"].values, prof_idx.loc[df.user_id, "active_end"].values
    df["outside_usual_hours"] = ((df.hour < s) | (df.hour > e)).astype(int)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    df.insert(0, "txn_id", [f"T{i:06d}" for i in range(len(df))])
    cols = ["txn_id", "user_id", "recipient_id", "device_id", "district"] + FEATURES + ["is_scam", "scam_type"]
    return df[cols], profiles


def generate_forwarding(seed=42):
    """Onward transfers used for network analysis.
    Mule wallets forward collected money to their ring's collector wallet (C..).
    Shops legitimately pay suppliers (B..), so the graph is not trivially 'only mules forward money'."""
    rng = np.random.default_rng(seed + 1)
    rows = []
    for m in range(N_MULES):
        for _ in range(rng.integers(2, 7)):
            rows.append((f"M{m:03d}", f"C{m % N_RINGS:02d}", round(float(rng.uniform(3000, 25000)), -1)))
    for s_ in range(N_SHOPS):
        for _ in range(rng.integers(1, 5)):
            rows.append((f"S{s_:03d}", f"B{rng.integers(0, 30):02d}", round(float(rng.uniform(2000, 25000)), -1)))
    return pd.DataFrame(rows, columns=["from_wallet", "to_wallet", "amount"])


ROLE = {"R": "person", "S": "shop", "M": "mule", "C": "collector", "B": "supplier"}


def anonymise(df, fwd, seed=42):
    """Replace internal IDs (which encode the role) with neutral wallet IDs like W48213.
    The true role of each wallet is kept in a separate ground-truth table that is used ONLY for evaluation."""
    rng = np.random.default_rng(seed + 2)
    ids = sorted(set(df.recipient_id) | set(fwd.from_wallet) | set(fwd.to_wallet))
    new = [f"W{x:05d}" for x in rng.choice(90000, len(ids), replace=False) + 10000]
    mp = dict(zip(ids, new))
    df = df.assign(recipient_id=df.recipient_id.map(mp))
    fwd = fwd.assign(from_wallet=fwd.from_wallet.map(mp), to_wallet=fwd.to_wallet.map(mp))
    roles = pd.DataFrame({"wallet_id": [mp[i] for i in ids], "role": [ROLE[i[0]] for i in ids]})
    return df, fwd, roles


def generate_all(n=60000, seed=42):
    df, profiles = generate(n, seed=seed)
    df, fwd, roles = anonymise(df, generate_forwarding(seed), seed)
    return df, profiles, fwd, roles


def write_all(folder="data", n=60000):
    os.makedirs(folder, exist_ok=True)
    df, profiles, fwd, roles = generate_all(n)
    df.to_csv(os.path.join(folder, "transactions.csv"), index=False)
    profiles.to_csv(os.path.join(folder, "user_profiles.csv"), index=False)
    fwd.to_csv(os.path.join(folder, "forwarding.csv"), index=False)
    roles.to_csv(os.path.join(folder, "wallet_roles_ground_truth.csv"), index=False)
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60000)
    args = ap.parse_args()
    df = write_all(folder="data/previous", n=args.n)
    print(f"Wrote {len(df):,} transfers for {N_USERS:,} customers (scam rate {df.is_scam.mean():.2%})")
    print(df.scam_type.value_counts().to_string())
